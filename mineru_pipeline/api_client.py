"""
mineru_pipeline.api_client
~~~~~~~~~~~~~~~~~~~~~~~~~~
MinerU Precise API (v4) client.

Workflow
--------
1. POST /api/v4/file-urls/batch  → get signed upload URL + batch_id
2. PUT file to signed OSS URL (no Content-Type header; bypass proxy for OSS)
3. System auto-submits parse job after upload completes
4. GET /api/v4/extract-results/batch/{batch_id}  → poll until done
5. Download full_zip_url → extract content_list.json + images

PDF size limit
--------------
MinerU enforces a 200-page limit per file.  If the PDF exceeds this,
fetch() automatically splits it into ≤200-page chunks, uploads each
chunk, and returns a list of output directories.

Usage
-----
    from mineru_pipeline.api_client import MinerUClient

    client = MinerUClient(token="your-token")
    out_dirs = client.fetch(pdf_path=Path("book.pdf"), dest=Path("resources/mineru"))
    # returns list[Path], one per chunk
"""

from __future__ import annotations

import io
import os
import shutil
import subprocess
import time
import zipfile
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

_BASE = "https://mineru.net"
_POLL_INTERVAL = 10   # seconds between status checks
_POLL_TIMEOUT  = 600  # seconds before giving up
_PAGE_LIMIT    = 190  # stay safely under the 200-page API limit


class MinerUAPIError(RuntimeError):
    pass


class MinerUClient:
    def __init__(
        self,
        token: str | None = None,
        *,
        enable_formula: bool = True,
        enable_table: bool = True,
        model_version: str = "vlm",
    ) -> None:
        self.token = token or os.environ.get("MINERU_API_TOKEN", "")
        if not self.token:
            raise MinerUAPIError(
                "MinerU API token required. "
                "Set MINERU_API_TOKEN env var or pass token= to MinerUClient."
            )
        self.enable_formula = enable_formula
        self.enable_table = enable_table
        self.model_version = model_version
        self._session = requests.Session()
        self._session.headers["Authorization"] = f"Bearer {self.token}"

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def fetch(self, pdf_path: Path, dest: Path) -> list[Path]:
        """
        Upload *pdf_path* to MinerU, wait for parsing, and extract results
        into *dest/<stem>_part<N>/*, one directory per chunk.

        Returns a list of output directory paths (usually one, unless the
        PDF was split due to the 200-page limit).
        """
        pdf_path = Path(pdf_path)
        dest = Path(dest)

        chunks = self._split_if_needed(pdf_path)

        # Upload all chunks and collect batch_ids
        batch_ids: list[tuple[str, str]] = []  # (chunk_stem, batch_id)
        for chunk_path in chunks:
            print(f"  [api] uploading {chunk_path.name} …")
            upload_url, batch_id = self._get_upload_url(chunk_path)
            self._upload_file(chunk_path, upload_url)
            batch_ids.append((chunk_path.stem, batch_id))
            print(f"  [api] uploaded → batch_id={batch_id}")

        # Poll all batches until done
        print(f"  [api] waiting for {len(batch_ids)} batch(es) …")
        zip_urls = self._poll_all(batch_ids)

        # Download and extract
        out_dirs: list[Path] = []
        for chunk_stem, _batch_id in batch_ids:
            zip_url = zip_urls[chunk_stem]
            print(f"  [api] downloading {chunk_stem} …")
            out_dir = dest / chunk_stem
            self._download_and_extract(zip_url, out_dir)
            out_dirs.append(out_dir)
            print(f"  [api] extracted → {out_dir}")

        # Clean up temp split files
        if len(chunks) > 1:
            for chunk in chunks:
                chunk.unlink(missing_ok=True)

        return out_dirs

    # ------------------------------------------------------------------
    # PDF splitting
    # ------------------------------------------------------------------

    def _split_if_needed(self, pdf_path: Path) -> list[Path]:
        """Return [pdf_path] if within limit, else split and return chunk paths."""
        try:
            from pypdf import PdfReader, PdfWriter
        except ImportError:
            raise MinerUAPIError(
                "pypdf is required for automatic PDF splitting. "
                "Install it with: pip install pypdf"
            )

        reader = PdfReader(pdf_path)
        total = len(reader.pages)
        if total <= _PAGE_LIMIT:
            return [pdf_path]

        print(f"  [api] PDF has {total} pages (limit {_PAGE_LIMIT}), splitting …")
        chunks: list[Path] = []
        stem = pdf_path.stem
        parent = pdf_path.parent

        for i, start in enumerate(range(0, total, _PAGE_LIMIT), 1):
            end = min(start + _PAGE_LIMIT, total)
            writer = PdfWriter()
            for p in range(start, end):
                writer.add_page(reader.pages[p])
            chunk_path = parent / f"{stem}_part{i}.pdf"
            with open(chunk_path, "wb") as f:
                writer.write(f)
            size_mb = chunk_path.stat().st_size / 1024 / 1024
            print(f"  [api]   part{i}: pages {start+1}-{end} ({size_mb:.1f}MB)")
            chunks.append(chunk_path)

        return chunks

    # ------------------------------------------------------------------
    # Step 1: get signed upload URL
    # ------------------------------------------------------------------

    def _get_upload_url(self, pdf_path: Path) -> tuple[str, str]:
        payload = {
            "files": [{"name": pdf_path.name, "data_id": pdf_path.stem}],
            "enable_formula": self.enable_formula,
            "enable_table": self.enable_table,
            "model_version": self.model_version,
        }
        resp = self._post("/api/v4/file-urls/batch", json=payload)
        data = resp["data"]
        batch_id: str = data["batch_id"]
        file_urls: list = data["file_urls"]
        if not file_urls:
            raise MinerUAPIError("No upload URL returned by /api/v4/file-urls/batch")
        # API returns a list of URL strings (not dicts)
        url = file_urls[0] if isinstance(file_urls[0], str) else file_urls[0]["url"]
        return url, batch_id

    # ------------------------------------------------------------------
    # Step 2: PUT file to signed OSS URL
    # ------------------------------------------------------------------

    def _upload_file(self, pdf_path: Path, upload_url: str) -> None:
        # OSS signed URLs are sensitive to Content-Type — send no Content-Type
        # header so it matches the empty string in the pre-signed signature.
        # Also bypass any local HTTP proxy, which can corrupt large PUT bodies.
        env = {**os.environ, "NO_PROXY": "*.aliyuncs.com", "no_proxy": "*.aliyuncs.com"}
        result = subprocess.run(
            [
                "curl", "-X", "PUT", upload_url,
                "-H", "Content-Type:",
                "--noproxy", "*",
                "--upload-file", str(pdf_path),
                "-s", "-o", "/dev/null",
                "-w", "%{http_code}",
            ],
            capture_output=True,
            text=True,
            env=env,
            timeout=300,
        )
        http_code = result.stdout.strip()
        if http_code != "200":
            raise MinerUAPIError(
                f"File upload failed: HTTP {http_code}\n{result.stderr[:200]}"
            )

    # ------------------------------------------------------------------
    # Step 3: poll all batches until done
    # ------------------------------------------------------------------

    def _poll_all(self, batch_ids: list[tuple[str, str]]) -> dict[str, str]:
        """Returns {chunk_stem: zip_url} for all completed batches."""
        pending = dict(batch_ids)  # stem → batch_id
        zip_urls: dict[str, str] = {}
        deadline = time.monotonic() + _POLL_TIMEOUT

        while pending and time.monotonic() < deadline:
            done_stems = []
            for stem, bid in pending.items():
                resp = self._get(f"/api/v4/extract-results/batch/{bid}")
                result = resp["data"]["extract_result"][0]
                state = result.get("state", "")
                if state == "done":
                    zip_url = result.get("full_zip_url", "")
                    if not zip_url:
                        raise MinerUAPIError(f"Batch {bid} done but full_zip_url missing")
                    zip_urls[stem] = zip_url
                    done_stems.append(stem)
                    print(f"  [api] {stem}: done")
                elif state == "failed":
                    err = result.get("err_msg", "unknown error")
                    raise MinerUAPIError(f"MinerU batch {bid} failed: {err}")
                else:
                    print(f"  [api] {stem}: {state}")
            for s in done_stems:
                del pending[s]
            if pending:
                time.sleep(_POLL_INTERVAL)

        if pending:
            raise MinerUAPIError(
                f"Timed out after {_POLL_TIMEOUT}s. Still pending: {list(pending)}"
            )
        return zip_urls

    # ------------------------------------------------------------------
    # Step 4: download ZIP and extract
    # ------------------------------------------------------------------

    def _download_and_extract(self, zip_url: str, out_dir: Path) -> None:
        r = requests.get(zip_url, timeout=300)
        if not r.ok:
            raise MinerUAPIError(
                f"ZIP download failed: HTTP {r.status_code} — {r.text[:200]}"
            )
        if out_dir.exists():
            if out_dir.is_dir():
                shutil.rmtree(out_dir)
            else:
                out_dir.unlink()
        out_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
            for member in zf.infolist():
                target = (out_dir / member.filename).resolve()
                if not target.is_relative_to(out_dir.resolve()):
                    raise MinerUAPIError(
                        f"Unsafe ZIP member path in MinerU result: {member.filename}"
                    )
            zf.extractall(out_dir)

    # ------------------------------------------------------------------
    # HTTP helpers
    # ------------------------------------------------------------------

    def _post(self, path: str, **kwargs) -> dict:
        r = self._session.post(f"{_BASE}{path}", timeout=60, **kwargs)
        return self._check(r)

    def _get(self, path: str) -> dict:
        r = self._session.get(f"{_BASE}{path}", timeout=30)
        return self._check(r)

    @staticmethod
    def _check(r: requests.Response) -> dict:
        r.raise_for_status()
        body = r.json()
        code = body.get("code", -1)
        if code != 0:
            msg = body.get("msg", body.get("message", str(body)))
            raise MinerUAPIError(f"MinerU API error (code={code}): {msg}")
        return body

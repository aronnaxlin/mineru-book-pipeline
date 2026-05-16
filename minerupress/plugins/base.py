from __future__ import annotations
from pathlib import Path


class ExportPlugin:
    """
    Base class for exporter plugins.

    Subclass and override any hooks you need.  All hooks have safe defaults
    (pass-through / no-op) so you only implement what you care about.
    """

    # ------------------------------------------------------------------
    # Image hooks
    # ------------------------------------------------------------------

    def on_image(self, item: dict, img_path: Path | None) -> bool:
        """
        Called for every image item before it is written to Markdown.

        Return False to drop the image entirely (e.g. QR codes).
        Return True to keep it.
        """
        return True

    # ------------------------------------------------------------------
    # Text hooks
    # ------------------------------------------------------------------

    def on_text(self, item: dict, text: str) -> str:
        """
        Called for every text-like item after basic conversion.

        Return the (possibly modified) text string.
        """
        return text

    # ------------------------------------------------------------------
    # Chapter hooks
    # ------------------------------------------------------------------

    def on_chapter_done(self, slug: str, lines: list[str]) -> list[str]:
        """
        Called after all items in a chapter have been converted.

        Receives the full list of output lines; return the (possibly
        modified) list.
        """
        return lines

    # ------------------------------------------------------------------
    # Export lifecycle hooks
    # ------------------------------------------------------------------

    def on_export_done(self, docs_out: Path) -> None:
        """
        Called once after all chapters have been written.

        Use for post-export actions such as deployment.
        docs_out is the Path passed as BookConfig.docs_out.
        """
        pass

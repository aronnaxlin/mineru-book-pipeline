from __future__ import annotations
from pathlib import Path

from .base import ExportPlugin

try:
    import cv2 as _cv2
    _DETECTOR = _cv2.QRCodeDetector()
    _AVAILABLE = True
except ImportError:
    _AVAILABLE = False


class QRFilterPlugin(ExportPlugin):
    """
    Drop images that are QR codes.

    Detection strategy: OpenCV QRCodeDetector.detect() (finder-pattern
    only, no decode required).  A max_side cap prevents false positives
    on large diagrams with grid-like patterns.

    Parameters
    ----------
    max_side : int
        Images larger than this on either dimension are never considered
        QR codes.  Default 250 covers all known course QR variants in
        MinerU output (typically 128–142 px wide, up to ~200 px tall when
        a caption is included in the crop).
    """

    def __init__(self, max_side: int = 250) -> None:
        self.max_side = max_side
        if not _AVAILABLE:
            import warnings
            warnings.warn(
                "opencv-python not installed; QRFilterPlugin is disabled. "
                "Run: pip install opencv-python",
                stacklevel=2,
            )

    def on_image(self, item: dict, img_path: Path | None) -> bool:
        if not _AVAILABLE or img_path is None or not img_path.exists():
            return True
        try:
            frame = _cv2.imread(str(img_path))
            if frame is None:
                return True
            h, w = frame.shape[:2]
            if max(w, h) > self.max_side:
                return True
            _, bbox = _DETECTOR.detect(frame)
            return bbox is None  # False (drop) when QR detected
        except Exception:
            return True

"""Render PDF pages and package them into a ZIP archive."""
from io import BytesIO
import zipfile

import fitz

from .validation import open_pdf, ConversionError
from . import MAX_OUTPUT_BYTES


def pdf_to_images(data: bytes, image_type: str = "PNG", dpi: int = 150) -> tuple[bytes, int]:
    kind = image_type.upper()
    if kind not in {"PNG", "JPG", "JPEG"}:
        raise ConversionError("Choose PNG or JPG output.")
    if not 72 <= int(dpi) <= 300:
        raise ConversionError("DPI must be between 72 and 300.")
    doc = open_pdf(data)
    try:
        archive = BytesIO()
        ext = "jpg" if kind in {"JPG", "JPEG"} else "png"
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
            for i, page in enumerate(doc, start=1):
                pix = page.get_pixmap(matrix=fitz.Matrix(dpi / 72, dpi / 72), alpha=False)
                zf.writestr(f"page-{i:03d}.{ext}", pix.tobytes(ext))
        payload = archive.getvalue()
        if len(payload) > MAX_OUTPUT_BYTES:
            raise ConversionError("The image archive exceeds the 200 MB output limit. Try a lower DPI or fewer pages.")
        return payload, doc.page_count
    finally:
        doc.close()

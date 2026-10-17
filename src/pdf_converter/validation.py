"""Input validation shared by the conversion functions."""
from io import BytesIO

import fitz

from . import MAX_FILE_BYTES, MAX_PAGES


class ConversionError(ValueError):
    """An input or conversion problem suitable for showing to a user."""


def check_size(data: bytes, label: str = "File") -> None:
    if not data:
        raise ConversionError(f"{label} is empty.")
    if len(data) > MAX_FILE_BYTES:
        raise ConversionError(f"{label} exceeds the 50 MB per-file limit.")


def open_pdf(data: bytes) -> fitz.Document:
    check_size(data, "PDF")
    try:
        doc = fitz.open(stream=data, filetype="pdf")
    except Exception as exc:
        raise ConversionError("This file is not a readable PDF.") from exc
    if doc.needs_pass:
        doc.close()
        raise ConversionError("This PDF is password-protected. Remove its password before converting.")
    if doc.page_count < 1:
        doc.close()
        raise ConversionError("This PDF contains no pages.")
    if doc.page_count > MAX_PAGES:
        doc.close()
        raise ConversionError(f"This PDF has more than the {MAX_PAGES}-page processing limit.")
    return doc


def image_bytes(image, label: str = "Image") -> bytes:
    data = image.getvalue() if hasattr(image, "getvalue") else bytes(image)
    check_size(data, label)
    return data


def image_format(data: bytes) -> str:
    from PIL import Image, UnidentifiedImageError
    try:
        with Image.open(BytesIO(data)) as im:
            fmt = (im.format or "").upper()
            im.verify()
    except (UnidentifiedImageError, OSError) as exc:
        raise ConversionError("The uploaded file is not a supported, readable image.") from exc
    if fmt not in {"JPEG", "PNG", "WEBP", "BMP", "TIFF"}:
        raise ConversionError(f"Unsupported image format: {fmt or 'unknown'}.")
    return fmt

"""Extract an inclusive page range from a PDF."""
import fitz

from . import MAX_OUTPUT_BYTES
from .validation import open_pdf, ConversionError


def split_pdf(data: bytes, start_page: int, end_page: int) -> tuple[bytes, int]:
    doc = open_pdf(data)
    try:
        if start_page < 1 or end_page < start_page or end_page > doc.page_count:
            raise ConversionError(f"Enter a range from 1 to {doc.page_count}, with the start page no greater than the end page.")
        out = fitz.open()
        try:
            out.insert_pdf(doc, from_page=start_page - 1, to_page=end_page - 1)
            payload = out.tobytes(garbage=3, deflate=True)
            if len(payload) > MAX_OUTPUT_BYTES:
                raise ConversionError("The extracted PDF exceeds the 200 MB output limit.")
            return payload, out.page_count
        finally:
            out.close()
    finally:
        doc.close()

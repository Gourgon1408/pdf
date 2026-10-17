"""Merge PDFs in the order provided."""
import fitz

from . import MAX_OUTPUT_BYTES
from .validation import open_pdf, ConversionError


def merge_pdfs(files: list[bytes]) -> bytes:
    if len(files) < 2:
        raise ConversionError("Select at least two PDF files to merge.")
    if len(files) > 20:
        raise ConversionError("You can merge up to 20 PDF files at a time.")
    output = fitz.open()
    opened = []
    try:
        for raw in files:
            doc = open_pdf(raw)
            opened.append(doc)
            output.insert_pdf(doc)
        if output.page_count > 1000:
            raise ConversionError("The merged document exceeds the 1,000-page output limit.")
        payload = output.tobytes(garbage=3, deflate=True)
        if len(payload) > MAX_OUTPUT_BYTES:
            raise ConversionError("The merged PDF exceeds the 200 MB output limit.")
        return payload
    finally:
        output.close()
        for doc in opened:
            doc.close()

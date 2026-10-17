"""Convert a text-based PDF to an editable DOCX using pdf2docx."""
from io import BytesIO

from . import MAX_OUTPUT_BYTES
from .validation import open_pdf, ConversionError


def pdf_to_word(data: bytes) -> bytes:
    doc = open_pdf(data)
    doc.close()
    try:
        from pdf2docx import Converter
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory(prefix="local-pdf-") as tmp:
            src, dst = Path(tmp) / "input.pdf", Path(tmp) / "output.docx"
            src.write_bytes(data)
            cv = Converter(str(src))
            try:
                cv.convert(str(dst), multi_processing=False)
            finally:
                cv.close()
            if not dst.exists() or dst.stat().st_size == 0:
                raise ConversionError("PDF to Word conversion did not produce a valid document.")
            if dst.stat().st_size > MAX_OUTPUT_BYTES:
                raise ConversionError("The generated Word document exceeds the 200 MB output limit.")
            return dst.read_bytes()
    except ConversionError:
        raise
    except Exception as exc:
        raise ConversionError("PDF to Word conversion failed. Complex layouts and scanned pages may not convert accurately; OCR is not included.") from exc

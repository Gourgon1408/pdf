"""Convert DOCX to PDF with local LibreOffice in headless mode."""
from pathlib import Path
import shutil
import subprocess
import tempfile

from . import MAX_FILE_BYTES, MAX_OUTPUT_BYTES
from .validation import ConversionError


def libreoffice_path() -> str | None:
    return shutil.which("libreoffice") or shutil.which("soffice")


def word_to_pdf(data: bytes) -> bytes:
    if not data:
        raise ConversionError("The Word document is empty.")
    if len(data) > MAX_FILE_BYTES:
        raise ConversionError("Word document exceeds the 50 MB per-file limit.")
    binary = libreoffice_path()
    if not binary:
        raise ConversionError("LibreOffice was not found. Install it locally, then restart the app.")
    try:
        with tempfile.TemporaryDirectory(prefix="local-word-") as tmp:
            folder = Path(tmp)
            source = folder / "input.docx"
            source.write_bytes(data)
            result = subprocess.run([binary, "--headless", "--convert-to", "pdf", "--outdir", str(folder), str(source)], capture_output=True, text=True, timeout=90, check=False)
            target = folder / "input.pdf"
            if result.returncode != 0 or not target.is_file() or target.stat().st_size == 0:
                detail = (result.stderr or result.stdout or "").strip()
                raise ConversionError(f"LibreOffice could not convert this document.{(' ' + detail[:250]) if detail else ''}")
            payload = target.read_bytes()
            if len(payload) > MAX_OUTPUT_BYTES:
                raise ConversionError("The generated PDF exceeds the 200 MB output limit.")
            if not payload.startswith(b"%PDF-"):
                raise ConversionError("LibreOffice produced an invalid PDF file.")
            return payload
    except subprocess.TimeoutExpired as exc:
        raise ConversionError("LibreOffice took too long. Try a smaller document.") from exc
    except ConversionError:
        raise
    except OSError as exc:
        raise ConversionError("LibreOffice could not be started. Check its installation.") from exc

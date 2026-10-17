# Paperplane PDF Converter

Paperplane is a Streamlit app with six PDF and image conversion tools. It processes documents with local Python libraries and LibreOffice; it does not call a third-party conversion API. When deployed to Render, processing happens on the Render service, not on a visitor's device. The service does not intentionally retain uploaded files: conversion working directories are temporary and removed after each job. Uploaded and generated data may remain in Streamlit's server memory while the visitor's session is active.

## Features

- Convert every PDF page to PNG or JPG at 72–300 DPI and download the results as a ZIP.
- Combine JPG, JPEG, PNG, WebP, BMP, and TIFF images into a PDF in upload order; transparent pixels are flattened onto white.
- Convert text-based PDFs to editable DOCX with pdf2docx. Complex layouts can need corrections; OCR is not included.
- Convert DOCX to PDF with LibreOffice Writer in headless mode.
- Merge PDFs in the displayed upload order and extract inclusive page ranges.
- Validate PDFs and images, reject password-protected PDFs, and clean up conversion working directories on success or failure.
- Default limits: 50 MB per file, 500 pages per PDF, 100 MB total input for image-to-PDF, 20 PDFs per merge, and 200 MB per output.

## Run locally on macOS

Use Python 3.11 or 3.12. Install LibreOffice if you need Word-to-PDF locally; the Docker image includes it automatically.

```bash
cd ~/my-python-project/pdf
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open <http://localhost:8501>. The local Streamlit server uses port 8501 by default. Press Control-C in the terminal to stop it.

## Test locally

```bash
cd ~/my-python-project/pdf
source .venv/bin/activate
python -m pytest -ra
```

Tests generate their own PDFs and images. The DOCX-to-PDF integration test skips only when no LibreOffice executable is present.

## Build and run with Docker

Install and start Docker Desktop, then run these commands from the project directory:

```bash
cd ~/my-python-project/pdf
docker build -t paperplane .
docker run --rm --name paperplane -p 10000:10000 -e PORT=10000 paperplane
```

Open <http://localhost:10000>. Docker installs LibreOffice Writer and fonts in the image, so no host LibreOffice installation is needed. The container runs as an unprivileged user, binds to `0.0.0.0`, limits uploads to 50 MB, hides Streamlit error details, and includes a Docker health check. Set a different `PORT` environment variable and publish the same host port to test another port, for example `-p 10001:10001 -e PORT=10001`.

## Deploy to Render

The project root contains a Dockerfile. Render's Docker runtime builds it and runs the Dockerfile `CMD`; the app binds to `0.0.0.0` on Render's `PORT` value (defaulting to 10000 in the image). See Render's [Docker deployment guide](https://render.com/docs/docker) and [web service port requirements](https://render.com/docs/web-services#port-binding).

1. Push this project to a Git repository accessible to Render.
2. In the Render Dashboard, choose **New → Web Service**, then connect that repository.
3. Set **Language** to **Docker**. If `pdf/` is a subdirectory in the connected repository, set the **Root Directory** to `pdf`; if it is the repository root, leave Root Directory blank.
4. Set **Dockerfile Path** to `./Dockerfile` relative to the selected root directory. Leave the Docker command and build command blank so Render uses the Dockerfile.
5. In **Advanced → Health Check Path**, set `/_stcore/health`.
6. Create the service. Render supplies `PORT`; no application secrets or external conversion API keys are required.

The service's generated `https://…onrender.com` address is the public URL. For HTTP health checks, Render accepts any 2xx or 3xx response from the configured path; see the [Render health check guide](https://render.com/docs/health-checks).

## Dependency notes

`requirements.txt` lists the application libraries and pytest. Streamlit, PyMuPDF (`fitz`), Pillow, python-docx, and pdf2docx are directly used by the app or its tests. pdf2docx brings its conversion dependencies (including OpenCV, NumPy, lxml, and fonttools) transitively through pip. LibreOffice is an operating-system package installed in the Docker image, not a pip package.

## Limitations and privacy

- PDF-to-Word recreates text and layout heuristically. Scanned PDFs are not OCR processed.
- Password-protected PDFs are rejected; the app does not bypass document security.
- Animated image formats use their first frame.
- On Render, uploaded documents are sent to and processed by the deployed Paperplane server. Conversion job directories are temporary, but Streamlit can keep upload/download objects in session memory until that session ends. Do not upload documents unless you trust the service operator.
- Render's container filesystem is ephemeral unless a persistent disk is explicitly added. This app does not require a persistent disk and should be deployed without one.
- Adjust limits in `src/pdf_converter/__init__.py` and Streamlit's upload limit in `.streamlit/config.toml` together.

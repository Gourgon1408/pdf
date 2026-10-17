FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=10000 \
    TMPDIR=/tmp/paperplane

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        fontconfig \
        fonts-dejavu-core \
        fonts-liberation \
        libreoffice-writer \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /tmp/paperplane /app/.streamlit \
    && useradd --create-home --uid 10001 --shell /usr/sbin/nologin appuser \
    && chown -R appuser:appuser /app /tmp/paperplane

COPY requirements.txt ./requirements.txt
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY app.py ./app.py
COPY src/ ./src/
COPY .streamlit/config.toml ./.streamlit/config.toml

ENV PYTHONPATH=/app/src

USER appuser

EXPOSE 10000

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.getenv('PORT', '10000') + '/_stcore/health', timeout=3).read()" || exit 1

CMD ["sh", "-c", "exec streamlit run app.py --server.address 0.0.0.0 --server.port ${PORT:-10000} --server.headless true"]

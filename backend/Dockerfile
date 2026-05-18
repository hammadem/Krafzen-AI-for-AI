# KRAFZEN AI backend — Python + Potrace + ODA File Converter (DWG).
# Render: set runtime to Docker, rootDir=backend. Build-time env: R2_* or DWG_ODA_DEB_URL.
# Local Apple Silicon: docker build --platform linux/amd64 ...

FROM python:3.12-slim-bookworm

ARG DWG_ODA_DEB_URL=
ARG R2_ACCESS_KEY_ID=
ARG R2_SECRET_ACCESS_KEY=
ARG R2_ENDPOINT_URL=
ARG R2_ODA_BUCKET=
ARG R2_ODA_OBJECT_KEY=

ENV DWG_ODA_DEB_URL=${DWG_ODA_DEB_URL} \
    R2_ACCESS_KEY_ID=${R2_ACCESS_KEY_ID} \
    R2_SECRET_ACCESS_KEY=${R2_SECRET_ACCESS_KEY} \
    R2_ENDPOINT_URL=${R2_ENDPOINT_URL} \
    R2_ODA_BUCKET=${R2_ODA_BUCKET} \
    R2_ODA_OBJECT_KEY=${R2_ODA_OBJECT_KEY}

RUN useradd -m -u 1000 appuser

WORKDIR /app

COPY docker /tmp/docker-build/
COPY docker/install_oda_file_converter.sh docker/fetch_and_install_oda.sh docker/download_oda_deb.py /tmp/

RUN chmod +x /tmp/install_oda_file_converter.sh /tmp/fetch_and_install_oda.sh \
    && apt-get update \
    && apt-get install -y --no-install-recommends potrace \
    && /tmp/fetch_and_install_oda.sh \
    && rm -rf /tmp/docker-build /tmp/*.sh /tmp/*.py /var/lib/apt/lists/*

ENV DWG_CONVERTER_TYPE=ODA \
    DWG_CONVERTER_CMD=ODAFileConverter \
    QT_QPA_PLATFORM=offscreen \
    QT_LOGGING_RULES=qt.qpa.plugin=false

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Render sets PORT; default 8000 for local docker run
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

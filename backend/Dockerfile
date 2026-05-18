# KRAFZEN AI backend — Python + Potrace + optional ODA File Converter (DWG).
# ODA Linux packages are x86_64; on Apple Silicon build hosts use: --platform linux/amd64
#
# Build with ODA (pick one):
#   docker build --platform linux/amd64 --build-arg DWG_ODA_DEB_URL="https://.../file.deb" ...
#   Place docker/oda-file-converter.deb in build context (gitignored) and build without the arg.

FROM python:3.12-slim

ARG DWG_ODA_DEB_URL=

RUN useradd -m -u 1000 appuser

WORKDIR /app

COPY docker/install_oda_file_converter.sh /tmp/install_oda_file_converter.sh
RUN chmod +x /tmp/install_oda_file_converter.sh

# Optional local .deb (filename fixed for predictable Docker COPY)
COPY docker /tmp/docker-build/

RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends potrace; \
    if [ -n "$DWG_ODA_DEB_URL" ]; then \
      /tmp/install_oda_file_converter.sh from-url "$DWG_ODA_DEB_URL"; \
    elif [ -f /tmp/docker-build/oda-file-converter.deb ]; then \
      /tmp/install_oda_file_converter.sh from-file /tmp/docker-build/oda-file-converter.deb; \
    else \
      echo "WARNING: ODA not installed — DWG export disabled in this image (set DWG_ODA_DEB_URL or add docker/oda-file-converter.deb)."; \
    fi; \
    rm -rf /tmp/docker-build; \
    rm -f /tmp/install_oda_file_converter.sh; \
    rm -rf /var/lib/apt/lists/*

ENV DWG_CONVERTER_TYPE=ODA
ENV DWG_CONVERTER_CMD=ODAFileConverter

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

RUN chown -R appuser:appuser /app

USER appuser

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

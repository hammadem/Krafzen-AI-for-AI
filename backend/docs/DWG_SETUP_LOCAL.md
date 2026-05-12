# DWG Setup (Local macOS)

This project generates DWG by converting the generated DXF using ODA File Converter.

## 1) Install ODA File Converter (macOS)

1. Open [ODA File Converter](https://www.opendesign.com/guestfiles/oda_file_converter)
2. Download the macOS build for your chip (`arm64` for Apple Silicon, `x64` for Intel)
3. Install `ODAFileConverter.app` into `/Applications`

Expected binary path:

`/Applications/ODAFileConverter.app/Contents/MacOS/ODAFileConverter`

## 2) Configure backend env

Add in `backend/.env` (or root `.env` depending on your local run):

```bash
DWG_CONVERTER_TYPE=ODA
DWG_CONVERTER_CMD=/Applications/ODAFileConverter.app/Contents/MacOS/ODAFileConverter
```

## 3) Validate converter

```bash
test -x /Applications/ODAFileConverter.app/Contents/MacOS/ODAFileConverter && echo "ODA ready"
```

## 4) Endpoints

- `POST /api/v1/chat/design-file` with body:
  - `image_url`
  - `file_type`: `dxf` or `dwg`
- `POST /api/v1/dxf/generate-and-store` with body:
  - `text`
  - `file_type`: `dxf` or `dwg`
  - `project_id` (optional)

## 5) Project download endpoint

- `GET /api/v1/dxf/download?project_id=<id>&file_type=dxf`
- `GET /api/v1/dxf/download?project_id=<id>&file_type=dwg`

## 6) Docker & Render (staging / production)

See [docker/README.md](../docker/README.md) for installing ODA in container images and on Render (build-time `DWG_ODA_DEB_URL`, Linux x64 `.deb`, optional `docker/oda-file-converter.deb` for local Docker builds).

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

**Recommended:** Run the API on Render with **`runtime: docker`** (see `render.yaml`). The image installs ODA via `apt`/`dpkg` with Qt headless plugins — same approach as Potrace in Docker.

On each Render service, set **build-time** env (used during `docker build`):

- `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_ENDPOINT_URL`, `R2_ODA_BUCKET`, `R2_ODA_OBJECT_KEY` (recommended), **or**
- `DWG_ODA_DEB_URL` — HTTPS URL to the Linux x64 `.deb`

After deploy, logs should show `Converting DXF → DWG via system ODA (Docker)`.

See [docker/README.md](../docker/README.md) for local `docker build` commands.

**Legacy native Python on Render** (`render_build_native.sh` + `.oda_bundle/`) is fragile because ODA needs Qt; prefer Docker for production/staging.

# DWG / ODA File Converter (Linux, Docker & Render)

DWG export uses **ODA File Converter** CLI (`ODAFileConverter`). The Linux package is distributed by [Open Design Alliance](https://www.opendesign.com/guestfiles/oda_file_converter) and must not be committed to this repository.

## Docker

ODA’s Linux builds are typically **x86_64**. On Apple Silicon hosts, build with:

```bash
docker build --platform linux/amd64 -t krafzen-backend \
  --build-arg DWG_ODA_DEB_URL="https://YOUR_HOST/oda-file-converter.deb" \
  -f Dockerfile .
```

Or place the downloaded `.deb` next to this folder as **`oda-file-converter.deb`** (gitignored) and build without the URL:

```bash
cp /path/to/your/oda-file-converter.deb docker/oda-file-converter.deb
docker build --platform linux/amd64 -t krafzen-backend -f Dockerfile ..
```

Runtime env (defaults are set in the Dockerfile when ODA is installed):

- `DWG_CONVERTER_TYPE=ODA`
- `DWG_CONVERTER_CMD=ODAFileConverter`

## Render (staging / production)

1. Download the **Linux x86_64** `.deb` from ODA (same page as above).
2. Upload the file to a **private** HTTPS location your build can reach (e.g. private S3 object URL, artifact storage, or signed URL).
3. In Render, add an environment variable used at **build** time:
   - `DWG_ODA_DEB_URL` = direct HTTPS URL to the `.deb` (mark as secret in Render).
4. Ensure the service runs on **amd64** (Render native Linux is x86_64).

`render_build_native.sh` installs ODA when `DWG_ODA_DEB_URL` is set and `apt-get` is available.

After deploy, set if needed:

- `DWG_CONVERTER_CMD=ODAFileConverter` (default if `ODAFileConverter` is on `PATH`)

## Ubuntu 22+ note

The install script creates `libxcb-util.so.0` → `libxcb-util.so.1` when required, per ODA’s common Linux guidance.

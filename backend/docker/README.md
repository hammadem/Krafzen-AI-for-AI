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
2. Upload the file to a **private** HTTPS location (e.g. Cloudflare R2 bucket).
3. **Recommended (Render):** add R2 API env vars on the API service (no presigned URL):

| Variable | Example |
|----------|---------|
| `R2_ACCESS_KEY_ID` | From R2 API token |
| `R2_SECRET_ACCESS_KEY` | From R2 API token |
| `R2_ENDPOINT_URL` | `https://YOUR_ACCOUNT_ID.r2.cloudflarestorage.com` |
| `R2_ODA_BUCKET` | `krafzen-build-private` |
| `R2_ODA_OBJECT_KEY` | `ODAFileConverter_QT6_lnxX64_8.3dll_27.1.deb` |

The API downloads the `.deb` at startup via boto3. Mark secrets in Render.

**Alternative:** presigned URL in `DWG_ODA_DEB_URL` (max **7 days**, `604800` seconds):

```bash
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_REGION=auto
aws s3 presign s3://krafzen-build-private/ODAFileConverter_QT6_lnxX64_8.3dll_27.1.deb \
  --endpoint-url "https://YOUR_ACCOUNT_ID.r2.cloudflarestorage.com" \
  --expires-in 604800 \
  --region auto
```

Paste the **full** URL with **no quotes**. If you still get HTTP 400, use the R2 API vars above instead.

4. Ensure the service runs on **amd64** (Render native Linux is x86_64).

`render_build_native.sh` installs ODA when `DWG_ODA_DEB_URL` is set and `apt-get` is available.

After deploy, set if needed:

- `DWG_CONVERTER_CMD=ODAFileConverter` (default if `ODAFileConverter` is on `PATH`)

## Ubuntu 22+ note

The install script creates `libxcb-util.so.0` → `libxcb-util.so.1` when required, per ODA’s common Linux guidance.

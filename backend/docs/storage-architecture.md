# Krafzen AI — Storage Architecture

## Overview

This document defines the storage organization, path conventions, naming structure, metadata handling, and retention planning for all files generated and managed by the Krafzen AI backend.

## 1. CAD Files (`dxf-files` bucket)

Owned and managed by **Tazwar**.

### Path Convention

```
{user_id}/{project_id}/{filename}
```

### Filename Convention

- **Auto-generated** (no filename provided):

```
project_{project_id}_{YYYYMMDD_HHMMSS}.{ext}
```

Example:

```
project_abc123_20250530_143022.dxf
```

- **Explicit filename** (passed in by caller):

```
{filename}.{ext}
```

Extension is appended automatically if missing.

### Supported Formats

| Format | Status       |
| ------ | ------------ |
| `.dxf` | ✅ Primary   |
| `.dwg` | ✅ Supported |
| `.ifc` | TODO         |

### Full Path Example

```
dxf-files/
  └── user_abc123/
      └── project_xyz456/
          └── project_xyz456_20250530_143022.dxf
```

### Public URL Structure

```
https://{supabase_project_id}.supabase.co/storage/v1/object/public/dxf-files/{user_id}/{project_id}/{filename}
```

### Artifact Handoff Flow

```
Tazwar job completes
  → StorageService.upload_cad_file() uploads file to dxf-files bucket
  → Returns public URL
  → PATCH /projects/{project_id} with { "dxf_url": "https://..." }
  → Yehor's API saves URL to project record
  → Sunny reads dxf_url from project and shows download button
```

## 2. General Uploads (`krafzen-files` bucket)

Owned and managed by **Yehor**.

### Path Convention

```
{user_id}/{project_id}/{file_id}.{ext}
```

### Purpose

- User-uploaded files
- Workspace assets
- Non-generated file attachments

### Metadata Tracked (files table)

| Column       | Type        | Description                     |
| ------------ | ----------- | ------------------------------- |
| `id`         | uuid        | Primary key                     |
| `job_id`     | uuid        | FK to jobs table                |
| `project_id` | uuid        | FK to projects table (nullable) |
| `bucket`     | text        | Storage bucket name             |
| `path`       | text        | Path within bucket              |
| `file_type`  | text        | dxf, dwg, ifc, pdf, etc.        |
| `mime_type`  | text        | MIME type of file               |
| `size_bytes` | int8        | File size                       |
| `created_at` | timestamptz | Upload timestamp                |

---

## 3. Project Record — URL Fields

After Tazwar uploads a CAD file, the public URL is stored directly on the project record for fast frontend access.

| Field       | Format              | Set By                          |
| ----------- | ------------------- | ------------------------------- |
| `dxf_url`   | Public Supabase URL | Tazwar via PATCH /projects/{id} |
| `dwg_url`   | Public Supabase URL | Tazwar via PATCH /projects/{id} |
| `ifc_url`   | Public Supabase URL | TODO:                           |
| `image_url` | Public Supabase URL | TODO: migration pending         |

---

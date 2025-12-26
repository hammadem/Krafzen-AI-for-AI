# How Users Get Generated DXF Design Files

## Overview
This document explains the different ways users can receive and access generated DXF design files from the KRAFZEN AI system.

## Current Implementation

### 1. **Direct API Download** (Immediate Download)
Users can get DXF files directly via API endpoints that return binary downloads:

#### Endpoint: `POST /api/v1/dxf/generate-from-text`
- **Purpose**: Generate DXF from text and download immediately
- **Request Body**:
  ```json
  {
    "text": "Draw a circle with radius 25mm at center 50,50",
    "file_type": "dxf",
    "additional_context": null
  }
  ```
- **Response**: Binary DXF file download (browser automatically downloads)
- **Use Case**: Quick one-off generation without storing

#### Endpoint: `POST /api/v1/dxf/generate`
- **Purpose**: Generate DXF from parsed instructions
- **Request Body**:
  ```json
  {
    "instructions": [
      {
        "command": "circle",
        "parameters": {"center": {"x": 50, "y": 50}, "radius": 25},
        "confidence": 0.9
      }
    ],
    "filename": "my_design.dxf"
  }
  ```
- **Response**: Binary DXF file download
- **Use Case**: When you already have parsed instructions

### 2. **Stored Files with Project Integration** (NEW - Recommended)
Users can generate and store DXF files linked to projects:

#### Endpoint: `POST /api/v1/dxf/generate-and-store`
- **Purpose**: Generate DXF, store in Supabase Storage, and link to project
- **Authentication**: Required (Bearer token)
- **Request Body**:
  ```json
  {
    "text": "Create a rectangle with width 200mm and height 100mm",
    "file_type": "dxf",
    "project_id": "uuid-of-project"
  }
  ```
- **Response**:
  ```json
  {
    "status": "success",
    "message": "DXF file generated successfully",
    "dxf_url": "https://your-project.supabase.co/storage/v1/object/public/dxf-files/user_id/project_id/file.dxf",
    "download_url": "/api/v1/dxf/download?project_id=uuid",
    "instructions_count": 1,
    "file_size": 36072,
    "is_valid": true
  }
  ```
- **What Happens**:
  1. Text is parsed into CAD instructions
  2. DXF file is generated
  3. File is uploaded to Supabase Storage (`dxf-files` bucket)
  4. Project's `dxf_url` field is updated
  5. Public URL is returned

#### Endpoint: `GET /api/v1/dxf/download?project_id={project_id}`
- **Purpose**: Download stored DXF file for a project
- **Authentication**: Required (Bearer token)
- **Response**: Binary DXF file download
- **Use Case**: Retrieve previously generated files

### 3. **Via Project API** (Frontend Integration)
Projects have a `dxf_url` field that can be accessed:

#### Endpoint: `GET /api/v1/projects/{project_id}`
- **Response includes**:
  ```json
  {
    "id": "project-uuid",
    "user_id": "user-uuid",
    "input_text": "Draw a circle...",
    "dxf_url": "https://your-project.supabase.co/storage/v1/object/public/dxf-files/...",
    "created_at": "2025-12-01T10:00:00Z"
  }
  ```
- **Frontend can**:
  - Display the `dxf_url` as a download link
  - Use it to fetch the file directly from Supabase Storage
  - Show download button in project history

## Complete User Workflow

### Option A: Direct Download (No Storage)
```
User Input (Text/Audio)
  ↓
Transcribe (if audio)
  ↓
POST /api/v1/dxf/generate-from-text
  ↓
Browser Downloads DXF File Immediately
```

### Option B: Store and Retrieve (Recommended)
```
User Input (Text/Audio)
  ↓
Create Project: POST /api/v1/projects/
  ↓
POST /api/v1/dxf/generate-and-store
  (with project_id)
  ↓
DXF Stored in Supabase Storage
Project.dxf_url Updated
  ↓
User can:
  - Download via GET /api/v1/dxf/download?project_id=...
  - Access via project.dxf_url
  - View in project history
```

## Frontend Integration Examples

### JavaScript/TypeScript (Fetch API)
```typescript
// Generate and store DXF
const response = await fetch('/api/v1/dxf/generate-and-store', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    text: userInput,
    file_type: 'dxf',
    project_id: projectId
  })
});

const data = await response.json();
// data.dxf_url contains the public URL
// data.download_url contains the API download endpoint

// Download file
const downloadResponse = await fetch(data.download_url, {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
const blob = await downloadResponse.blob();
const url = window.URL.createObjectURL(blob);
const a = document.createElement('a');
a.href = url;
a.download = 'design.dxf';
a.click();
```

### Direct Supabase Storage Access
```typescript
// If you have the dxf_url from project
const dxfUrl = project.dxf_url; // Public URL from Supabase Storage
// Can be used directly in <a> tag or fetched
```

## File Storage Structure

Files are stored in Supabase Storage with the following structure:
```
dxf-files/
  └── {user_id}/
      └── {project_id}/
          └── project_{project_id}_{timestamp}.dxf
```

## Setup Requirements

### Supabase Storage Bucket
1. Create a bucket named `dxf-files` in Supabase Dashboard
2. Set bucket to **Public** (for public URLs) or configure RLS policies
3. Configure CORS if needed for direct browser access

### Environment Variables
Ensure these are set in `.env`:
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

## Security Considerations

1. **Authentication**: All storage endpoints require authentication
2. **Access Control**: Files are organized by `user_id` to prevent unauthorized access
3. **Public URLs**: If bucket is public, URLs are accessible to anyone with the link
4. **RLS Policies**: Consider implementing Row Level Security for additional protection

## Error Handling

- **503 Service Unavailable**: DXF generator or storage service not configured
- **404 Not Found**: DXF file doesn't exist for the project
- **401 Unauthorized**: User not authenticated or doesn't own the project
- **400 Bad Request**: Invalid input or parsing failed

## Best Practices

1. **Use `generate-and-store`** for production workflows
2. **Use `generate-from-text`** for quick tests or one-off generations
3. **Store project_id** when generating to enable file retrieval
4. **Check `dxf_url`** in project data before generating to avoid duplicates
5. **Handle errors gracefully** and provide user feedback

## Future Enhancements

- [ ] File versioning (multiple DXF files per project)
- [ ] File preview/thumbnail generation
- [ ] Batch download (multiple projects)
- [ ] File sharing (generate temporary signed URLs)
- [ ] File deletion endpoint
- [ ] Storage quota management










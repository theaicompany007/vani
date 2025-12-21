# Google Drive Integration Setup Guide

This guide details how to set up Google Drive integration to sync documents (PDF, DOCX, TXT, MD) to the RAG knowledge base in Project VANI.

## 🎯 Overview

The Google Drive integration allows super administrators to browse their Google Drive, select specific files, and trigger an on-demand synchronization process. Files are organized into RAG collections based on their folder structure in Google Drive.

## 🔑 Authentication: Google Service Account

Access to Google Drive is managed via a **Google Service Account**. This provides secure, programmatic access without requiring user interaction for each sync.

### Setup Steps:

1. **Create a Google Cloud Project**:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/).
   - Create a new project or select an existing one.

2. **Enable Google Drive API**:
   - In the Google Cloud Console, navigate to "APIs & Services" > "Enabled APIs & Services".
   - Click "+ ENABLE APIS AND SERVICES".
   - Search for "Google Drive API" and enable it.

3. **Create a Service Account**:
   - In the Google Cloud Console, go to "IAM & Admin" > "Service Accounts".
   - Click "+ CREATE SERVICE ACCOUNT".
   - Provide a Service account name (e.g., `vani-drive-sync`).
   - Grant the service account the role `Storage Object Viewer` or a custom role with minimal permissions for Drive access.
   - Click "Done".

4. **Generate a JSON Key**:
   - After creating the service account, click on its email address.
   - Go to the "Keys" tab.
   - Click "ADD KEY" > "Create new key".
   - Select "JSON" as the key type and click "CREATE".
   - A JSON file will be downloaded. **Keep this file secure and do not commit it to your repository.**

5. **Share Google Drive Folders/Files with the Service Account**:
   - Go to your Google Drive (theaicompany007@gmail.com).
   - For each folder or file you want the service account to access, share it with the service account's email address (found in the downloaded JSON key file, under `client_email`).
   - Grant "Viewer" access to the service account.

## ⚙️ Environment Variables

Add one of the following to your `.env.local` file:

```bash
# Option 1: Embed the entire JSON key as a string (recommended for cloud environments)
GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON='{"type":"service_account","project_id":"...","private_key_id":"...","private_key":"-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n","client_email":"your-service-account@your-project.iam.gserviceaccount.com","client_id":"...","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_x509_cert_url":"https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com","universe_domain":"googleapis.com"}'

# Option 2: Provide a path to the JSON key file (recommended for local development/VMs)
# GOOGLE_DRIVE_SERVICE_ACCOUNT_PATH=C:\path\to\your\service-account-key.json
```

**Important**: 
- If using `GOOGLE_DRIVE_SERVICE_ACCOUNT_PATH`, ensure the path is accessible by the application and the file is present on the server/VM.
- For Windows paths, use forward slashes or escaped backslashes: `C:/path/to/key.json` or `C:\\path\\to\\key.json`

## 📁 Collection Naming Convention

Files synced from Google Drive will be organized into RAG collections based on their folder structure:

- **Root level files**: `google_drive_research_company_profiles`
- **Files within a folder**: `{sanitized_folder_name}_company_profiles` (e.g., `vani_research_company_profiles`)
- **Files within nested folders**: `{parent_folder}_{child_folder}_company_profiles` (e.g., `the_ai_company_vani_company_profiles`)

**Sanitization**: Folder names are converted to lowercase, spaces and special characters are replaced with underscores, and segments are truncated to a maximum of 50 characters.

## 🖥️ Using the Google Drive UI

### Access

1. Log in as a **super user**
2. Navigate to the **Admin** tab
3. Click on the **Google Drive** sub-tab

### Features

- **Browse Folders**: Click on folder names to navigate into them
- **Select Files**: Use checkboxes to select files for synchronization (folders cannot be selected)
- **Sync Selected**: Click "Sync Selected" to upload files to the RAG knowledge base
- **View Results**: After syncing, view detailed results showing which files succeeded or failed

### Supported File Types

- PDF (`.pdf`)
- Microsoft Word (`.docx`)
- Text files (`.txt`)
- Markdown (`.md`)
- Google Docs (exported as DOCX)

## 🔧 Troubleshooting

### "Service account not configured"
- Ensure `GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON` or `GOOGLE_DRIVE_SERVICE_ACCOUNT_PATH` is set in `.env.local`
- Verify the JSON is valid JSON format
- Restart the Flask application after adding environment variables

### "Permission denied" or "File not found"
- Check that the service account email has access to the Drive folder
- Verify the service account has the Drive API scope enabled
- Ensure you've shared the folder/file with the service account email address

### "Failed to download file"
- Ensure the file is not in a restricted folder
- Check that the file type is supported (PDF, DOCX, TXT, MD)
- Verify the file is not corrupted

### "RAG upload failed"
- Verify `RAG_SERVICE_URL` and `RAG_API_KEY` are configured in `.env.local`
- Check RAG service health: `GET {RAG_SERVICE_URL}/health`
- Review application logs for detailed error messages

### "No text extracted"
- Some PDFs may be image-based (scanned documents) and require OCR
- Verify the file is not corrupted
- Check that the file actually contains text content

## 🔒 Security Best Practices

1. **Service Account Scope**: Uses `drive.readonly` scope (read-only access)
2. **Folder Sharing**: Only share specific folders needed, not entire Drive
3. **Key Storage**: Store keys in environment variables, never in code
4. **Access Control**: API endpoints require super user authentication
5. **Audit**: Monitor Drive API usage in Google Cloud Console

## 📊 API Endpoints

### `GET /api/drive/list`
List files and folders from Google Drive.

**Query Parameters:**
- `folderId` (optional): Folder ID to list (default: 'root')

**Response:**
```json
{
  "success": true,
  "files": [
    {
      "id": "file_id",
      "name": "filename.pdf",
      "mimeType": "application/pdf",
      "size": 12345,
      "modifiedTime": "2024-01-01T00:00:00Z",
      "isFolder": false,
      "webViewLink": "https://drive.google.com/..."
    }
  ]
}
```

### `GET /api/drive/file/<file_id>`
Get metadata for a specific file.

**Response:**
```json
{
  "success": true,
  "id": "file_id",
  "name": "filename.pdf",
  "mimeType": "application/pdf",
  "size": 12345,
  "modifiedTime": "2024-01-01T00:00:00Z",
  "isFolder": false,
  "webViewLink": "https://drive.google.com/...",
  "parents": ["parent_folder_id"]
}
```

### `POST /api/drive/sync`
Sync selected files from Google Drive to RAG.

**Request Body:**
```json
{
  "fileIds": ["file_id_1", "file_id_2"]
}
```

**Response:**
```json
{
  "success": true,
  "synced": 2,
  "failed": 0,
  "collections": ["vani_research_company_profiles"],
  "results": [
    {
      "id": "file_id_1",
      "name": "document.pdf",
      "success": true,
      "chunks": 15,
      "collection": "vani_research_company_profiles"
    }
  ]
}
```

## 📦 Dependencies

The following Python packages are required (already in `requirements.txt`):
- `google-api-python-client>=2.110.0`
- `google-auth>=2.25.2`

Install with:
```bash
pip install -r requirements.txt
```

## 🔄 Workflow

1. **Setup**: Configure service account and environment variables
2. **Share**: Share Google Drive folders with service account
3. **Browse**: Use the Admin UI to browse and select files
4. **Sync**: Click "Sync Selected" to upload files to RAG
5. **Verify**: Check sync results and query RAG to verify content

## 📝 Notes

- Files are processed synchronously (one at a time) to avoid overwhelming the RAG service
- Text is chunked into 500-character segments with 50-character overlap
- Each chunk includes metadata about the source file and folder path
- Files are temporarily downloaded to extract text, then cleaned up automatically
- Google Docs are automatically exported as DOCX before processing


import os
import json
import logging
from io import BytesIO
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import mimetypes

# Scopes required for Google Drive API
SCOPES = ['https://www.googleapis.com/auth/drive']

logger = logging.getLogger(__name__)

class GoogleDriveService:
    def __init__(self):
        self.folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "").strip()
        self.client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
        self.client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
        self.refresh_token = os.getenv("GOOGLE_REFRESH_TOKEN", "").strip()
        
        # Log limited info for debugging in Render
        if self.folder_id:
            logger.info(f"GoogleDriveService initialized with folder_id: {self.folder_id[:5]}...{self.folder_id[-5:]}")
        else:
            logger.warning("GoogleDriveService initialized WITHOUT GOOGLE_DRIVE_FOLDER_ID")
            
        self.service = self._authenticate()

    def _authenticate(self):
        """Authenticates using OAuth2 Client ID, Secret, and Refresh Token."""
        try:
            if not (self.client_id and self.client_secret and self.refresh_token):
                logger.warning("Missing OAuth2 credentials (ID, Secret, or Token). Upload will fail.")
                return None
            
            creds = Credentials(
                token=None,  # Will be refreshed
                refresh_token=self.refresh_token,
                client_id=self.client_id,
                client_secret=self.client_secret,
                token_uri="https://oauth2.googleapis.com/token",
                scopes=SCOPES
            )
            
            # Force refresh to ensure token is valid
            creds.refresh(Request())
            
            return build('drive', 'v3', credentials=creds)
        except Exception as e:
            logger.error(f"Failed to authenticate with Google Drive OAuth2: {e}")
            return None

    def upload_file(self, file_stream: BytesIO, filename: str) -> dict:
        """Uploads a file stream to the specified Google Drive folder with retries."""
        if not self.service:
            return {"success": False, "error": "Google Drive service not authenticated (check OAuth2 credentials)"}

        # Reset stream position to beginning
        file_stream.seek(0)
        
        file_metadata = {
            'name': filename,
            'parents': [self.folder_id] if self.folder_id else []
        }
        
        # Guess mimetype based on filename or fallback
        mime_type = mimetypes.guess_type(filename)[0] or 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        
        media = MediaIoBaseUpload(
            file_stream, 
            mimetype=mime_type,
            resumable=False
        )

        max_retries = 3
        last_error = None
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    logger.info(f"Retrying upload to Drive (attempt {attempt + 1}/{max_retries})...")
                
                # Reset stream for each attempt
                file_stream.seek(0)
                
                file = self.service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id, webViewLink, webContentLink'
                ).execute()
                
                file_id = file.get('id')
                
                # Set permissions so anyone with the link can access (reader)
                try:
                    self.service.permissions().create(
                        fileId=file_id,
                        body={'type': 'anyone', 'role': 'reader'}
                    ).execute()
                    logger.info(f"Permissions set to 'public reader' for file {file_id}")
                except Exception as perm_error:
                    logger.warning(f"Could not set public permissions for file {file_id}: {perm_error}")

                view_link = file.get('webViewLink')
                download_link = file.get('webContentLink')
                logger.info(f"Successfully uploaded to Drive. ID: {file_id}")
                
                return {
                    "success": True,
                    "file_id": file_id,
                    "view_link": view_link,
                    "download_link": download_link
                }
            except Exception as e:
                last_error = e
                logger.warning(f"Upload attempt {attempt + 1} failed: {e}")
                # Optional: add a small delay if needed
                import time
                time.sleep(1)
        
        logger.error(f"Failed to upload to Google Drive after {max_retries} attempts: {last_error}")
        return {"success": False, "error": str(last_error)}

# Singleton instance
drive_service = GoogleDriveService()

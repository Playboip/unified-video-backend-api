"""
Backblaze B2 Storage Service
Handles file uploads, downloads, and management for AI Video Remix
"""

import os
import logging
import uuid
from typing import Dict, Any, Optional
from werkzeug.datastructures import FileStorage
from b2sdk.v2 import InMemoryAccountInfo, B2Api
from b2sdk.v2.exception import B2Error

logger = logging.getLogger(__name__)

class BackblazeService:
    """
    Backblaze B2 storage service for AI Video Remix files
    Free tier: 10GB storage + 1GB daily download
    """
    
    def __init__(self):
        self.application_key_id = os.getenv('B2_APPLICATION_KEY_ID')
        self.application_key = os.getenv('B2_APPLICATION_KEY')
        self.bucket_name = os.getenv('B2_BUCKET_NAME')
        self.bucket_id = os.getenv('B2_BUCKET_ID')
        
        if not all([self.application_key_id, self.application_key, self.bucket_name]):
            raise ValueError("Backblaze B2 credentials not properly configured")
        
        # Initialize B2 API
        self.info = InMemoryAccountInfo()
        self.api = B2Api(self.info)
        self.bucket = None
        
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Backblaze B2 and get bucket"""
        try:
            self.api.authorize_account("production", self.application_key_id, self.application_key)
            self.bucket = self.api.get_bucket_by_name(self.bucket_name)
            logger.info(f"Successfully connected to Backblaze B2 bucket: {self.bucket_name}")
        except B2Error as e:
            logger.error(f"Failed to authenticate with Backblaze B2: {e}")
            raise
    
    def upload_file(self, file: FileStorage, user_id: str, file_type: str) -> Dict[str, Any]:
        """
        Upload file to Backblaze B2
        
        Args:
            file: File to upload
            user_id: ID of the user uploading
            file_type: Type of file (remix_video, remix_audio, etc.)
        
        Returns:
            Dict with file URL and metadata
        """
        try:
            # Generate unique filename
            file_extension = self._get_file_extension(file.filename)
            unique_filename = f"{user_id}/{file_type}/{uuid.uuid4()}{file_extension}"
            
            # Prepare file content
            file_content = file.read()
            file.seek(0)  # Reset file pointer
            
            # Upload to B2
            file_info = self.bucket.upload_bytes(
                data_bytes=file_content,
                file_name=unique_filename,
                content_type=file.content_type or 'application/octet-stream',
                file_infos={
                    'user_id': user_id,
                    'file_type': file_type,
                    'original_filename': file.filename or 'unknown'
                }
            )
            
            # Get download URL
            download_url = self.api.get_download_url_for_fileid(file_info.id_)
            
            result = {
                'success': True,
                'file_id': file_info.id_,
                'file_name': unique_filename,
                'download_url': download_url,
                'file_size': len(file_content),
                'content_type': file.content_type,
                'service': 'backblaze',
                'metadata': {
                    'user_id': user_id,
                    'file_type': file_type,
                    'original_filename': file.filename
                }
            }
            
            logger.info(f"Successfully uploaded file to Backblaze B2: {unique_filename}")
            return result
        
        except B2Error as e:
            logger.error(f"Backblaze B2 upload failed: {e}")
            raise Exception(f"B2 upload failed: {str(e)}")
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            raise Exception(f"Upload failed: {str(e)}")
    
    def delete_file(self, file_url: str) -> bool:
        """
        Delete file from Backblaze B2
        
        Args:
            file_url: URL of file to delete
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Extract file ID from URL
            file_id = self._extract_file_id_from_url(file_url)
            if not file_id:
                logger.error(f"Could not extract file ID from URL: {file_url}")
                return False
            
            # Get file info and delete
            file_version = self.api.get_file_info(file_id)
            self.api.delete_file_version(file_id, file_version.file_name)
            
            logger.info(f"Successfully deleted file from Backblaze B2: {file_id}")
            return True
        
        except B2Error as e:
            logger.error(f"Failed to delete file from Backblaze B2: {e}")
            return False
        except Exception as e:
            logger.error(f"Delete operation failed: {e}")
            return False
    
    def get_signed_url(self, file_url: str, expiry_hours: int = 24) -> str:
        """
        Get signed download URL (Backblaze B2 URLs are already signed)
        
        Args:
            file_url: Original file URL
            expiry_hours: Hours until expiry (not used for B2)
        
        Returns:
            Download URL
        """
        # Backblaze B2 download URLs are already authorized
        # For additional security, you could implement authorization tokens
        return file_url
    
    def _get_file_extension(self, filename: Optional[str]) -> str:
        """Extract file extension from filename"""
        if not filename:
            return ''
        
        if '.' in filename:
            return '.' + filename.rsplit('.', 1)[1].lower()
        return ''
    
    def _extract_file_id_from_url(self, file_url: str) -> Optional[str]:
        """Extract file ID from Backblaze B2 download URL"""
        try:
            # B2 download URLs typically contain the file ID
            # Format: https://f{bucket_id}.backblazeb2.com/file/{bucket_name}/{file_name}
            # or: https://s3.{region}.backblazeb2.com/{bucket_name}/{file_name}
            
            # This is a simplified extraction - in practice, you'd store file IDs in your database
            # For now, return None to indicate we need the file ID from database
            return None
        except Exception:
            return None
    
    def get_bucket_info(self) -> Dict[str, Any]:
        """Get information about the B2 bucket"""
        try:
            bucket_info = {
                'bucket_name': self.bucket_name,
                'bucket_id': self.bucket_id,
                'bucket_type': self.bucket.bucket_type,
                'service': 'Backblaze B2',
                'free_tier_limit': '10GB storage + 1GB daily download'
            }
            return bucket_info
        except Exception as e:
            logger.error(f"Failed to get bucket info: {e}")
            return {}
    
    def list_files(self, user_id: str, file_type: Optional[str] = None, limit: int = 100) -> list:
        """
        List files for a user
        
        Args:
            user_id: User ID to filter by
            file_type: Optional file type filter
            limit: Maximum number of files to return
        
        Returns:
            List of file information
        """
        try:
            # Build prefix for user files
            prefix = f"{user_id}/"
            if file_type:
                prefix += f"{file_type}/"
            
            files = []
            for file_version, _ in self.bucket.ls(folder_to_list=prefix, recursive=True):
                file_info = {
                    'file_id': file_version.id_,
                    'file_name': file_version.file_name,
                    'size': file_version.size,
                    'upload_timestamp': file_version.upload_timestamp,
                    'content_type': file_version.content_type,
                    'download_url': self.api.get_download_url_for_fileid(file_version.id_)
                }
                files.append(file_info)
                
                if len(files) >= limit:
                    break
            
            return files
        
        except B2Error as e:
            logger.error(f"Failed to list files: {e}")
            return []
        except Exception as e:
            logger.error(f"List files operation failed: {e}")
            return []


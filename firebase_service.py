"""
Firebase Storage Service
Handles file uploads for shared resources like user avatars and templates
"""

import os
import logging
import uuid
import json
from typing import Dict, Any, Optional
from werkzeug.datastructures import FileStorage
import firebase_admin
from firebase_admin import credentials, storage
from firebase_admin.exceptions import FirebaseError

logger = logging.getLogger(__name__)

class FirebaseService:
    """
    Firebase storage service for shared resources
    Free tier: 5GB storage + 1GB daily download
    """
    
    def __init__(self):
        self.project_id = os.getenv('FIREBASE_PROJECT_ID')
        self.credentials_path = os.getenv('FIREBASE_CREDENTIALS_PATH')
        self.bucket_name = os.getenv('FIREBASE_STORAGE_BUCKET')
        
        if not self.project_id:
            raise ValueError("Firebase project ID not configured")
        
        # Initialize Firebase Admin SDK
        self._initialize_firebase()
        
        # Get storage bucket
        self.bucket = storage.bucket(self.bucket_name) if self.bucket_name else storage.bucket()
        
        logger.info(f"Successfully configured Firebase Storage: {self.project_id}")
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            # Check if Firebase is already initialized
            firebase_admin.get_app()
            logger.info("Firebase already initialized")
        except ValueError:
            # Initialize Firebase
            if self.credentials_path and os.path.exists(self.credentials_path):
                cred = credentials.Certificate(self.credentials_path)
                firebase_admin.initialize_app(cred, {
                    'storageBucket': self.bucket_name or f"{self.project_id}.appspot.com"
                })
            else:
                # Use default credentials (for deployment environments)
                firebase_admin.initialize_app()
            
            logger.info("Firebase initialized successfully")
    
    def upload_file(self, file: FileStorage, user_id: str, file_type: str) -> Dict[str, Any]:
        """
        Upload file to Firebase Storage
        
        Args:
            file: File to upload
            user_id: ID of the user uploading
            file_type: Type of file (user_avatar, template_thumbnail, etc.)
        
        Returns:
            Dict with file URL and metadata
        """
        try:
            # Generate unique filename
            file_extension = self._get_file_extension(file.filename)
            unique_filename = f"{file_type}/{user_id}/{uuid.uuid4()}{file_extension}"
            
            # Create blob
            blob = self.bucket.blob(unique_filename)
            
            # Set metadata
            blob.metadata = {
                'user_id': user_id,
                'file_type': file_type,
                'original_filename': file.filename or 'unknown'
            }
            
            # Upload file
            file_content = file.read()
            file.seek(0)  # Reset file pointer
            
            blob.upload_from_string(
                file_content,
                content_type=file.content_type or 'application/octet-stream'
            )
            
            # Make blob publicly readable (for avatars and thumbnails)
            blob.make_public()
            
            # Get download URL
            download_url = blob.public_url
            
            result = {
                'success': True,
                'file_name': unique_filename,
                'download_url': download_url,
                'file_size': len(file_content),
                'content_type': file.content_type,
                'service': 'firebase',
                'metadata': {
                    'user_id': user_id,
                    'file_type': file_type,
                    'original_filename': file.filename,
                    'blob_name': unique_filename
                }
            }
            
            logger.info(f"Successfully uploaded file to Firebase Storage: {unique_filename}")
            return result
        
        except FirebaseError as e:
            logger.error(f"Firebase upload failed: {e}")
            raise Exception(f"Firebase upload failed: {str(e)}")
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            raise Exception(f"Upload failed: {str(e)}")
    
    def delete_file(self, file_url: str) -> bool:
        """
        Delete file from Firebase Storage
        
        Args:
            file_url: URL of file to delete
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Extract blob name from URL
            blob_name = self._extract_blob_name_from_url(file_url)
            if not blob_name:
                logger.error(f"Could not extract blob name from URL: {file_url}")
                return False
            
            # Delete blob
            blob = self.bucket.blob(blob_name)
            blob.delete()
            
            logger.info(f"Successfully deleted file from Firebase Storage: {blob_name}")
            return True
        
        except FirebaseError as e:
            logger.error(f"Failed to delete file from Firebase Storage: {e}")
            return False
        except Exception as e:
            logger.error(f"Delete operation failed: {e}")
            return False
    
    def get_signed_url(self, file_url: str, expiry_hours: int = 24) -> str:
        """
        Get signed download URL for private files
        
        Args:
            file_url: Original file URL
            expiry_hours: Hours until expiry
        
        Returns:
            Signed download URL
        """
        try:
            # Extract blob name from URL
            blob_name = self._extract_blob_name_from_url(file_url)
            if not blob_name:
                return file_url
            
            # Generate signed URL
            blob = self.bucket.blob(blob_name)
            signed_url = blob.generate_signed_url(
                expiration=expiry_hours * 3600,  # Convert hours to seconds
                method='GET'
            )
            
            return signed_url
        
        except Exception as e:
            logger.error(f"Failed to generate signed URL: {e}")
            return file_url
    
    def _get_file_extension(self, filename: Optional[str]) -> str:
        """Extract file extension from filename"""
        if not filename:
            return ''
        
        if '.' in filename:
            return '.' + filename.rsplit('.', 1)[1].lower()
        return ''
    
    def _extract_blob_name_from_url(self, file_url: str) -> Optional[str]:
        """Extract blob name from Firebase Storage URL"""
        try:
            # Firebase Storage URLs format: 
            # https://firebasestorage.googleapis.com/v0/b/{bucket}/o/{blob_name}?{params}
            if 'firebasestorage.googleapis.com' in file_url:
                # Extract blob name from URL
                parts = file_url.split('/o/')
                if len(parts) > 1:
                    blob_part = parts[1].split('?')[0]  # Remove query parameters
                    # URL decode the blob name
                    import urllib.parse
                    blob_name = urllib.parse.unquote(blob_part)
                    return blob_name
            
            return None
        except Exception:
            return None
    
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
            prefix = f"{file_type}/{user_id}/" if file_type else f"*/{user_id}/"
            
            files = []
            blobs = self.bucket.list_blobs(prefix=prefix, max_results=limit)
            
            for blob in blobs:
                file_info = {
                    'file_name': blob.name,
                    'size': blob.size,
                    'upload_timestamp': blob.time_created.isoformat() if blob.time_created else None,
                    'content_type': blob.content_type,
                    'download_url': blob.public_url,
                    'metadata': blob.metadata or {}
                }
                files.append(file_info)
            
            return files
        
        except FirebaseError as e:
            logger.error(f"Failed to list files: {e}")
            return []
        except Exception as e:
            logger.error(f"List files operation failed: {e}")
            return []
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get information about the Firebase service"""
        return {
            'project_id': self.project_id,
            'service': 'Firebase Storage',
            'free_tier_limit': '5GB storage + 1GB daily download',
            'features': [
                'Real-time file synchronization',
                'Secure file access',
                'Global CDN',
                'Automatic scaling'
            ]
        }


"""
Storage Manager for Video Editor Backend
Handles multiple storage services: Backblaze B2, Cloudinary, Firebase
"""

import os
import logging
from typing import Optional, Dict, Any
from werkzeug.datastructures import FileStorage

# Import storage services
from .backblaze_service import BackblazeService
from .cloudinary_service import CloudinaryService
from .firebase_service import FirebaseService

logger = logging.getLogger(__name__)

class StorageManager:
    """
    Manages multiple storage services and routes files to appropriate storage
    based on file type and service availability
    """
    
    def __init__(self):
        self.backblaze = None
        self.cloudinary = None
        self.firebase = None
        
        # Initialize available services
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize available storage services based on configuration"""
        try:
            # Initialize Backblaze B2 (for AI Video Remix)
            if all([
                os.getenv('B2_APPLICATION_KEY_ID'),
                os.getenv('B2_APPLICATION_KEY'),
                os.getenv('B2_BUCKET_NAME')
            ]):
                self.backblaze = BackblazeService()
                logger.info("Backblaze B2 service initialized")
            else:
                logger.warning("Backblaze B2 credentials not found")
        
        except Exception as e:
            logger.error(f"Failed to initialize Backblaze: {e}")
        
        try:
            # Initialize Cloudinary (for Vibe Video Editor)
            if all([
                os.getenv('CLOUDINARY_CLOUD_NAME'),
                os.getenv('CLOUDINARY_API_KEY'),
                os.getenv('CLOUDINARY_API_SECRET')
            ]):
                self.cloudinary = CloudinaryService()
                logger.info("Cloudinary service initialized")
            else:
                logger.warning("Cloudinary credentials not found")
        
        except Exception as e:
            logger.error(f"Failed to initialize Cloudinary: {e}")
        
        try:
            # Initialize Firebase (for shared resources)
            if os.getenv('FIREBASE_CREDENTIALS_PATH'):
                self.firebase = FirebaseService()
                logger.info("Firebase service initialized")
            else:
                logger.warning("Firebase credentials not found")
        
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
    
    def upload_file(self, file: FileStorage, file_type: str, user_id: str, 
                   service_preference: Optional[str] = None) -> Dict[str, Any]:
        """
        Upload file to appropriate storage service
        
        Args:
            file: File to upload
            file_type: Type of file (remix_video, editor_video, user_avatar, etc.)
            user_id: ID of the user uploading the file
            service_preference: Preferred storage service (optional)
        
        Returns:
            Dict containing upload result with URL and metadata
        """
        try:
            # Route based on file type
            if file_type in ['remix_video', 'remix_audio', 'remix_thumbnail']:
                if self.backblaze:
                    return self.backblaze.upload_file(file, user_id, file_type)
                else:
                    # Fallback to Cloudinary if Backblaze not available
                    if self.cloudinary:
                        return self.cloudinary.upload_file(file, user_id, file_type)
            
            elif file_type in ['editor_video', 'editor_audio', 'editor_image', 'project_export']:
                if self.cloudinary:
                    return self.cloudinary.upload_file(file, user_id, file_type)
                else:
                    # Fallback to Backblaze if Cloudinary not available
                    if self.backblaze:
                        return self.backblaze.upload_file(file, user_id, file_type)
            
            elif file_type in ['user_avatar', 'template_thumbnail', 'effect_preview']:
                if self.firebase:
                    return self.firebase.upload_file(file, user_id, file_type)
                else:
                    # Fallback to other services
                    if self.cloudinary:
                        return self.cloudinary.upload_file(file, user_id, file_type)
                    elif self.backblaze:
                        return self.backblaze.upload_file(file, user_id, file_type)
            
            else:
                # Auto-select based on file size and availability
                return self._auto_select_storage(file, user_id, file_type)
        
        except Exception as e:
            logger.error(f"Failed to upload file: {e}")
            raise Exception(f"Upload failed: {str(e)}")
    
    def _auto_select_storage(self, file: FileStorage, user_id: str, file_type: str) -> Dict[str, Any]:
        """Auto-select storage service based on availability and file size"""
        file_size = self._get_file_size(file)
        
        # For large files (>100MB), prefer Cloudinary or Backblaze
        if file_size > 100 * 1024 * 1024:  # 100MB
            if self.cloudinary:
                return self.cloudinary.upload_file(file, user_id, file_type)
            elif self.backblaze:
                return self.backblaze.upload_file(file, user_id, file_type)
        
        # For small files, prefer Firebase
        elif file_size < 10 * 1024 * 1024:  # 10MB
            if self.firebase:
                return self.firebase.upload_file(file, user_id, file_type)
        
        # Default fallback order
        for service in [self.cloudinary, self.backblaze, self.firebase]:
            if service:
                return service.upload_file(file, user_id, file_type)
        
        raise Exception("No storage service available")
    
    def _get_file_size(self, file: FileStorage) -> int:
        """Get file size in bytes"""
        file.seek(0, 2)  # Seek to end
        size = file.tell()
        file.seek(0)  # Reset to beginning
        return size
    
    def delete_file(self, file_url: str, service_type: str = None) -> bool:
        """
        Delete file from storage service
        
        Args:
            file_url: URL of file to delete
            service_type: Type of storage service (optional, will auto-detect)
        
        Returns:
            True if deletion successful, False otherwise
        """
        try:
            # Auto-detect service from URL if not specified
            if not service_type:
                if 'backblazeb2.com' in file_url or 'b2-api.com' in file_url:
                    service_type = 'backblaze'
                elif 'cloudinary.com' in file_url:
                    service_type = 'cloudinary'
                elif 'firebase' in file_url or 'googleapis.com' in file_url:
                    service_type = 'firebase'
            
            # Delete from appropriate service
            if service_type == 'backblaze' and self.backblaze:
                return self.backblaze.delete_file(file_url)
            elif service_type == 'cloudinary' and self.cloudinary:
                return self.cloudinary.delete_file(file_url)
            elif service_type == 'firebase' and self.firebase:
                return self.firebase.delete_file(file_url)
            
            logger.warning(f"Could not determine storage service for URL: {file_url}")
            return False
        
        except Exception as e:
            logger.error(f"Failed to delete file {file_url}: {e}")
            return False
    
    def get_download_url(self, file_url: str, expiry_hours: int = 24) -> str:
        """
        Get signed download URL for file
        
        Args:
            file_url: Original file URL
            expiry_hours: Hours until URL expires
        
        Returns:
            Signed download URL
        """
        try:
            # Determine service and get signed URL
            if 'backblazeb2.com' in file_url and self.backblaze:
                return self.backblaze.get_signed_url(file_url, expiry_hours)
            elif 'cloudinary.com' in file_url and self.cloudinary:
                return self.cloudinary.get_signed_url(file_url, expiry_hours)
            elif 'firebase' in file_url and self.firebase:
                return self.firebase.get_signed_url(file_url, expiry_hours)
            
            # Return original URL if no signing needed
            return file_url
        
        except Exception as e:
            logger.error(f"Failed to get signed URL for {file_url}: {e}")
            return file_url
    
    def get_service_status(self) -> Dict[str, bool]:
        """Get status of all storage services"""
        return {
            'backblaze': self.backblaze is not None,
            'cloudinary': self.cloudinary is not None,
            'firebase': self.firebase is not None
        }
    
    def get_storage_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about storage services and their usage"""
        info = {}
        
        if self.backblaze:
            info['backblaze'] = {
                'service': 'Backblaze B2',
                'free_tier': '10GB storage + 1GB daily download',
                'use_case': 'AI Video Remix files',
                'status': 'active'
            }
        
        if self.cloudinary:
            info['cloudinary'] = {
                'service': 'Cloudinary',
                'free_tier': '25GB storage + 25GB bandwidth/month',
                'use_case': 'Vibe Video Editor files',
                'status': 'active'
            }
        
        if self.firebase:
            info['firebase'] = {
                'service': 'Firebase Storage',
                'free_tier': '5GB storage + 1GB daily download',
                'use_case': 'User avatars and shared resources',
                'status': 'active'
            }
        
        return info


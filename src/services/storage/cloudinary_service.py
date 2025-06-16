"""
Cloudinary Storage Service
Handles file uploads, downloads, and video processing for Vibe Video Editor
"""

import os
import logging
import uuid
from typing import Dict, Any, Optional
from werkzeug.datastructures import FileStorage
import cloudinary
import cloudinary.uploader
import cloudinary.utils
from cloudinary.exceptions import Error as CloudinaryError

logger = logging.getLogger(__name__)

class CloudinaryService:
    """
    Cloudinary storage service for Vibe Video Editor files
    Free tier: 25GB storage + 25GB bandwidth/month
    """
    
    def __init__(self):
        self.cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME')
        self.api_key = os.getenv('CLOUDINARY_API_KEY')
        self.api_secret = os.getenv('CLOUDINARY_API_SECRET')
        
        if not all([self.cloud_name, self.api_key, self.api_secret]):
            raise ValueError("Cloudinary credentials not properly configured")
        
        # Configure Cloudinary
        cloudinary.config(
            cloud_name=self.cloud_name,
            api_key=self.api_key,
            api_secret=self.api_secret,
            secure=True
        )
        
        logger.info(f"Successfully configured Cloudinary: {self.cloud_name}")
    
    def upload_file(self, file: FileStorage, user_id: str, file_type: str) -> Dict[str, Any]:
        """
        Upload file to Cloudinary
        
        Args:
            file: File to upload
            user_id: ID of the user uploading
            file_type: Type of file (editor_video, editor_audio, etc.)
        
        Returns:
            Dict with file URL and metadata
        """
        try:
            # Generate unique public ID
            file_extension = self._get_file_extension(file.filename)
            public_id = f"{user_id}/{file_type}/{uuid.uuid4()}"
            
            # Determine resource type
            resource_type = self._get_resource_type(file.content_type, file_extension)
            
            # Upload options
            upload_options = {
                'public_id': public_id,
                'resource_type': resource_type,
                'folder': f"video-editor/{user_id}",
                'context': {
                    'user_id': user_id,
                    'file_type': file_type,
                    'original_filename': file.filename or 'unknown'
                },
                'tags': [file_type, user_id]
            }
            
            # Add video-specific options
            if resource_type == 'video':
                upload_options.update({
                    'eager': [
                        {'width': 300, 'height': 200, 'crop': 'fill', 'format': 'jpg'},  # Thumbnail
                        {'width': 640, 'height': 480, 'crop': 'limit', 'format': 'mp4'}  # Preview
                    ],
                    'eager_async': True
                })
            
            # Upload file
            result = cloudinary.uploader.upload(file, **upload_options)
            
            # Process result
            response = {
                'success': True,
                'public_id': result['public_id'],
                'file_name': public_id,
                'download_url': result['secure_url'],
                'file_size': result['bytes'],
                'content_type': file.content_type,
                'service': 'cloudinary',
                'metadata': {
                    'user_id': user_id,
                    'file_type': file_type,
                    'original_filename': file.filename,
                    'resource_type': resource_type,
                    'format': result.get('format'),
                    'width': result.get('width'),
                    'height': result.get('height'),
                    'duration': result.get('duration')  # For videos
                }
            }
            
            # Add thumbnail URL for videos
            if resource_type == 'video' and 'eager' in result:
                thumbnails = [eager for eager in result['eager'] if eager.get('format') == 'jpg']
                if thumbnails:
                    response['thumbnail_url'] = thumbnails[0]['secure_url']
            
            logger.info(f"Successfully uploaded file to Cloudinary: {public_id}")
            return response
        
        except CloudinaryError as e:
            logger.error(f"Cloudinary upload failed: {e}")
            raise Exception(f"Cloudinary upload failed: {str(e)}")
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            raise Exception(f"Upload failed: {str(e)}")
    
    def delete_file(self, file_url: str) -> bool:
        """
        Delete file from Cloudinary
        
        Args:
            file_url: URL of file to delete
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Extract public ID from URL
            public_id = self._extract_public_id_from_url(file_url)
            if not public_id:
                logger.error(f"Could not extract public ID from URL: {file_url}")
                return False
            
            # Determine resource type
            resource_type = self._determine_resource_type_from_url(file_url)
            
            # Delete file
            result = cloudinary.uploader.destroy(public_id, resource_type=resource_type)
            
            if result.get('result') == 'ok':
                logger.info(f"Successfully deleted file from Cloudinary: {public_id}")
                return True
            else:
                logger.warning(f"Cloudinary delete result: {result}")
                return False
        
        except CloudinaryError as e:
            logger.error(f"Failed to delete file from Cloudinary: {e}")
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
            # Extract public ID from URL
            public_id = self._extract_public_id_from_url(file_url)
            if not public_id:
                return file_url
            
            # Generate signed URL
            signed_url = cloudinary.utils.private_download_url(
                public_id,
                format='auto',
                expires_at=expiry_hours * 3600  # Convert hours to seconds
            )
            
            return signed_url
        
        except Exception as e:
            logger.error(f"Failed to generate signed URL: {e}")
            return file_url
    
    def transform_video(self, public_id: str, transformations: Dict[str, Any]) -> str:
        """
        Apply transformations to video
        
        Args:
            public_id: Cloudinary public ID of the video
            transformations: Transformation parameters
        
        Returns:
            URL of transformed video
        """
        try:
            # Build transformation URL
            transformed_url = cloudinary.utils.cloudinary_url(
                public_id,
                resource_type='video',
                **transformations
            )[0]
            
            return transformed_url
        
        except Exception as e:
            logger.error(f"Failed to transform video: {e}")
            raise Exception(f"Video transformation failed: {str(e)}")
    
    def generate_thumbnail(self, video_public_id: str, time_offset: float = 0) -> str:
        """
        Generate thumbnail from video at specific time
        
        Args:
            video_public_id: Public ID of the video
            time_offset: Time offset in seconds
        
        Returns:
            Thumbnail URL
        """
        try:
            thumbnail_url = cloudinary.utils.cloudinary_url(
                video_public_id,
                resource_type='video',
                format='jpg',
                start_offset=f"{time_offset}s",
                width=300,
                height=200,
                crop='fill'
            )[0]
            
            return thumbnail_url
        
        except Exception as e:
            logger.error(f"Failed to generate thumbnail: {e}")
            raise Exception(f"Thumbnail generation failed: {str(e)}")
    
    def _get_resource_type(self, content_type: Optional[str], file_extension: str) -> str:
        """Determine Cloudinary resource type from content type and extension"""
        if content_type:
            if content_type.startswith('video/'):
                return 'video'
            elif content_type.startswith('audio/'):
                return 'video'  # Cloudinary treats audio as video
            elif content_type.startswith('image/'):
                return 'image'
        
        # Fallback to extension
        video_extensions = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv']
        audio_extensions = ['.mp3', '.wav', '.aac', '.ogg', '.m4a', '.flac']
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg']
        
        ext = file_extension.lower()
        if ext in video_extensions or ext in audio_extensions:
            return 'video'
        elif ext in image_extensions:
            return 'image'
        
        return 'raw'  # Default for other file types
    
    def _get_file_extension(self, filename: Optional[str]) -> str:
        """Extract file extension from filename"""
        if not filename:
            return ''
        
        if '.' in filename:
            return '.' + filename.rsplit('.', 1)[1].lower()
        return ''
    
    def _extract_public_id_from_url(self, file_url: str) -> Optional[str]:
        """Extract public ID from Cloudinary URL"""
        try:
            # Cloudinary URLs format: https://res.cloudinary.com/{cloud_name}/{resource_type}/upload/{public_id}.{format}
            parts = file_url.split('/')
            if 'cloudinary.com' in file_url and len(parts) >= 6:
                # Find the upload part and extract public ID
                upload_index = -1
                for i, part in enumerate(parts):
                    if part == 'upload':
                        upload_index = i
                        break
                
                if upload_index >= 0 and upload_index + 1 < len(parts):
                    public_id_with_format = parts[upload_index + 1]
                    # Remove format extension
                    public_id = public_id_with_format.rsplit('.', 1)[0]
                    return public_id
            
            return None
        except Exception:
            return None
    
    def _determine_resource_type_from_url(self, file_url: str) -> str:
        """Determine resource type from Cloudinary URL"""
        if '/video/upload/' in file_url:
            return 'video'
        elif '/image/upload/' in file_url:
            return 'image'
        elif '/raw/upload/' in file_url:
            return 'raw'
        return 'auto'
    
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
            # Build search expression
            search_expression = f"folder:video-editor/{user_id}"
            if file_type:
                search_expression += f" AND tags:{file_type}"
            
            # Search for files
            result = cloudinary.Search().expression(search_expression).max_results(limit).execute()
            
            files = []
            for resource in result.get('resources', []):
                file_info = {
                    'public_id': resource['public_id'],
                    'file_name': resource['public_id'],
                    'size': resource['bytes'],
                    'upload_timestamp': resource['created_at'],
                    'content_type': resource.get('resource_type'),
                    'download_url': resource['secure_url'],
                    'format': resource.get('format'),
                    'width': resource.get('width'),
                    'height': resource.get('height'),
                    'duration': resource.get('duration')
                }
                files.append(file_info)
            
            return files
        
        except CloudinaryError as e:
            logger.error(f"Failed to list files: {e}")
            return []
        except Exception as e:
            logger.error(f"List files operation failed: {e}")
            return []
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get information about the Cloudinary service"""
        return {
            'cloud_name': self.cloud_name,
            'service': 'Cloudinary',
            'free_tier_limit': '25GB storage + 25GB bandwidth/month',
            'features': [
                'Video processing and transformation',
                'Automatic thumbnail generation',
                'Format conversion',
                'Quality optimization',
                'Responsive delivery'
            ]
        }


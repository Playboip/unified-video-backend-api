"""
Video Processing Service
Handles video processing operations using FFmpeg for both video editors
"""

import os
import logging
import subprocess
import tempfile
import uuid
from typing import Dict, Any, Optional, List
from werkzeug.datastructures import FileStorage

logger = logging.getLogger(__name__)

class VideoProcessor:
    """
    Video processing service using FFmpeg
    Handles operations for both AI Video Remix and Vibe Video Editor
    """
    
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
        self._check_ffmpeg()
    
    def _check_ffmpeg(self):
        """Check if FFmpeg is available"""
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                logger.info("FFmpeg is available")
            else:
                raise Exception("FFmpeg not working properly")
        except Exception as e:
            logger.error(f"FFmpeg not available: {e}")
            raise Exception("FFmpeg is required for video processing")
    
    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """
        Get video information using FFprobe
        
        Args:
            video_path: Path to video file
        
        Returns:
            Dict with video metadata
        """
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                raise Exception(f"FFprobe failed: {result.stderr}")
            
            import json
            probe_data = json.loads(result.stdout)
            
            # Extract video stream info
            video_stream = None
            audio_stream = None
            
            for stream in probe_data.get('streams', []):
                if stream.get('codec_type') == 'video' and not video_stream:
                    video_stream = stream
                elif stream.get('codec_type') == 'audio' and not audio_stream:
                    audio_stream = stream
            
            info = {
                'duration': float(probe_data.get('format', {}).get('duration', 0)),
                'size': int(probe_data.get('format', {}).get('size', 0)),
                'format_name': probe_data.get('format', {}).get('format_name', ''),
                'bit_rate': int(probe_data.get('format', {}).get('bit_rate', 0))
            }
            
            if video_stream:
                info.update({
                    'width': int(video_stream.get('width', 0)),
                    'height': int(video_stream.get('height', 0)),
                    'fps': eval(video_stream.get('r_frame_rate', '0/1')),
                    'video_codec': video_stream.get('codec_name', ''),
                    'video_bitrate': int(video_stream.get('bit_rate', 0))
                })
            
            if audio_stream:
                info.update({
                    'audio_codec': audio_stream.get('codec_name', ''),
                    'audio_bitrate': int(audio_stream.get('bit_rate', 0)),
                    'sample_rate': int(audio_stream.get('sample_rate', 0)),
                    'channels': int(audio_stream.get('channels', 0))
                })
            
            return info
        
        except Exception as e:
            logger.error(f"Failed to get video info: {e}")
            raise Exception(f"Video analysis failed: {str(e)}")
    
    def generate_thumbnail(self, video_path: str, time_offset: float = 0, 
                          width: int = 300, height: int = 200) -> str:
        """
        Generate thumbnail from video
        
        Args:
            video_path: Path to video file
            time_offset: Time offset in seconds
            width: Thumbnail width
            height: Thumbnail height
        
        Returns:
            Path to generated thumbnail
        """
        try:
            output_path = os.path.join(self.temp_dir, f"thumb_{uuid.uuid4()}.jpg")
            
            cmd = [
                'ffmpeg', '-i', video_path,
                '-ss', str(time_offset),
                '-vframes', '1',
                '-vf', f'scale={width}:{height}',
                '-y', output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                raise Exception(f"Thumbnail generation failed: {result.stderr}")
            
            return output_path
        
        except Exception as e:
            logger.error(f"Failed to generate thumbnail: {e}")
            raise Exception(f"Thumbnail generation failed: {str(e)}")
    
    def convert_video(self, input_path: str, output_format: str = 'mp4',
                     width: Optional[int] = None, height: Optional[int] = None,
                     bitrate: Optional[str] = None) -> str:
        """
        Convert video to different format/quality
        
        Args:
            input_path: Path to input video
            output_format: Output format (mp4, webm, etc.)
            width: Output width (optional)
            height: Output height (optional)
            bitrate: Output bitrate (optional, e.g., '1M')
        
        Returns:
            Path to converted video
        """
        try:
            output_path = os.path.join(self.temp_dir, f"converted_{uuid.uuid4()}.{output_format}")
            
            cmd = ['ffmpeg', '-i', input_path]
            
            # Add video filters
            filters = []
            if width and height:
                filters.append(f'scale={width}:{height}')
            
            if filters:
                cmd.extend(['-vf', ','.join(filters)])
            
            # Add bitrate
            if bitrate:
                cmd.extend(['-b:v', bitrate])
            
            # Add codec settings for web compatibility
            if output_format == 'mp4':
                cmd.extend(['-c:v', 'libx264', '-c:a', 'aac', '-movflags', '+faststart'])
            elif output_format == 'webm':
                cmd.extend(['-c:v', 'libvpx-vp9', '-c:a', 'libopus'])
            
            cmd.extend(['-y', output_path])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                raise Exception(f"Video conversion failed: {result.stderr}")
            
            return output_path
        
        except Exception as e:
            logger.error(f"Failed to convert video: {e}")
            raise Exception(f"Video conversion failed: {str(e)}")
    
    def extract_audio(self, video_path: str, output_format: str = 'mp3') -> str:
        """
        Extract audio from video
        
        Args:
            video_path: Path to video file
            output_format: Audio format (mp3, wav, etc.)
        
        Returns:
            Path to extracted audio
        """
        try:
            output_path = os.path.join(self.temp_dir, f"audio_{uuid.uuid4()}.{output_format}")
            
            cmd = [
                'ffmpeg', '-i', video_path,
                '-vn',  # No video
                '-acodec', 'libmp3lame' if output_format == 'mp3' else 'copy',
                '-y', output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0:
                raise Exception(f"Audio extraction failed: {result.stderr}")
            
            return output_path
        
        except Exception as e:
            logger.error(f"Failed to extract audio: {e}")
            raise Exception(f"Audio extraction failed: {str(e)}")
    
    def merge_audio_video(self, video_path: str, audio_path: str) -> str:
        """
        Merge audio and video files
        
        Args:
            video_path: Path to video file
            audio_path: Path to audio file
        
        Returns:
            Path to merged video
        """
        try:
            output_path = os.path.join(self.temp_dir, f"merged_{uuid.uuid4()}.mp4")
            
            cmd = [
                'ffmpeg', '-i', video_path, '-i', audio_path,
                '-c:v', 'copy', '-c:a', 'aac',
                '-map', '0:v:0', '-map', '1:a:0',
                '-shortest',  # End when shortest input ends
                '-y', output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                raise Exception(f"Audio/video merge failed: {result.stderr}")
            
            return output_path
        
        except Exception as e:
            logger.error(f"Failed to merge audio/video: {e}")
            raise Exception(f"Audio/video merge failed: {str(e)}")
    
    def trim_video(self, video_path: str, start_time: float, duration: float) -> str:
        """
        Trim video to specific duration
        
        Args:
            video_path: Path to video file
            start_time: Start time in seconds
            duration: Duration in seconds
        
        Returns:
            Path to trimmed video
        """
        try:
            output_path = os.path.join(self.temp_dir, f"trimmed_{uuid.uuid4()}.mp4")
            
            cmd = [
                'ffmpeg', '-i', video_path,
                '-ss', str(start_time),
                '-t', str(duration),
                '-c', 'copy',  # Copy without re-encoding for speed
                '-y', output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0:
                raise Exception(f"Video trimming failed: {result.stderr}")
            
            return output_path
        
        except Exception as e:
            logger.error(f"Failed to trim video: {e}")
            raise Exception(f"Video trimming failed: {str(e)}")
    
    def add_text_overlay(self, video_path: str, text: str, 
                        position: str = 'center', duration: Optional[float] = None) -> str:
        """
        Add text overlay to video
        
        Args:
            video_path: Path to video file
            text: Text to overlay
            position: Position (center, top, bottom, etc.)
            duration: Duration of overlay (None for entire video)
        
        Returns:
            Path to video with text overlay
        """
        try:
            output_path = os.path.join(self.temp_dir, f"text_overlay_{uuid.uuid4()}.mp4")
            
            # Position mapping
            position_map = {
                'center': '(w-text_w)/2:(h-text_h)/2',
                'top': '(w-text_w)/2:50',
                'bottom': '(w-text_w)/2:h-text_h-50',
                'top-left': '50:50',
                'top-right': 'w-text_w-50:50',
                'bottom-left': '50:h-text_h-50',
                'bottom-right': 'w-text_w-50:h-text_h-50'
            }
            
            pos = position_map.get(position, position_map['center'])
            
            # Build drawtext filter
            drawtext = f"drawtext=text='{text}':fontsize=24:fontcolor=white:x={pos}"
            if duration:
                drawtext += f":enable='between(t,0,{duration})'"
            
            cmd = [
                'ffmpeg', '-i', video_path,
                '-vf', drawtext,
                '-c:a', 'copy',
                '-y', output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                raise Exception(f"Text overlay failed: {result.stderr}")
            
            return output_path
        
        except Exception as e:
            logger.error(f"Failed to add text overlay: {e}")
            raise Exception(f"Text overlay failed: {str(e)}")
    
    def cleanup_temp_file(self, file_path: str):
        """Clean up temporary file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.debug(f"Cleaned up temp file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temp file {file_path}: {e}")
    
    def get_supported_formats(self) -> Dict[str, List[str]]:
        """Get supported input and output formats"""
        return {
            'input_video': ['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv', '3gp'],
            'input_audio': ['mp3', 'wav', 'aac', 'ogg', 'm4a', 'flac'],
            'output_video': ['mp4', 'webm', 'avi', 'mov'],
            'output_audio': ['mp3', 'wav', 'aac', 'ogg']
        }


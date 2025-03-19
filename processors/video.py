import os
from pytube import YouTube
from moviepy.editor import VideoFileClip
import tempfile
import logging
from typing import Tuple, Optional, Dict, Any
import time
import requests
from urllib.parse import urlparse, parse_qs
import yt_dlp
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import json
from bs4 import BeautifulSoup
from .transcription import transcribe_audio
from .action_points import extract_action_points
import subprocess

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_temp_dir() -> str:
    """Create a temporary directory for processing files"""
    return tempfile.mkdtemp()

def setup_chrome_driver():
    """Setup undetected Chrome driver with appropriate options"""
    options = uc.ChromeOptions()
    options.add_argument("--headless=new")  # Use new headless mode
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument('--disable-features=VizDisplayCompositor')
    options.add_argument("--disable-web-security")
    options.add_argument("--allow-running-insecure-content")
    
    try:
        driver = uc.Chrome(options=options)
        driver.set_page_load_timeout(30)
        driver.implicitly_wait(10)
        return driver
    except Exception as e:
        logger.error(f"Failed to create undetected Chrome driver: {str(e)}")
        raise

def extract_loom_video_url(driver, url):
    """Extract video URL from Loom page"""
    logger.info("Attempting to extract Loom video URL...")
    try:
        # Wait for the page to load completely
        driver.get(url)
        time.sleep(5)  # Initial wait
        
        try:
            # Try to click any play button if present
            play_button = driver.find_element(By.CSS_SELECTOR, "[data-testid='play-button']")
            play_button.click()
            time.sleep(2)
        except:
            pass
            
        # Execute JavaScript to force video load
        driver.execute_script("""
            var videos = document.getElementsByTagName('video');
            for(var i = 0; i < videos.length; i++) {
                videos[i].play();
                videos[i].pause();
            }
        """)
        
        # Wait for network requests to complete
        time.sleep(3)
        
        # Get all network requests
        logs = driver.execute_script("""
            var performance = window.performance || window.mozPerformance || window.msPerformance || window.webkitPerformance || {};
            var entries = performance.getEntries() || [];
            return entries.map(function(entry) {
                return {
                    name: entry.name,
                    type: entry.initiatorType,
                    duration: entry.duration
                };
            });
        """)
        
        # Look for video URLs in network requests
        for entry in logs:
            if isinstance(entry, dict) and 'name' in entry:
                url = entry['name']
                if '/video/' in url.lower() and not 'thumbnail' in url.lower():
                    if any(ext in url.lower() for ext in ['.mp4', '.m3u8', '.ts']):
                        return url
        
        # If no video found in network requests, try DOM
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Look for video element with specific attributes
        for video in soup.find_all('video'):
            src = video.get('src') or video.get('data-src')
            if src and '/video/' in src.lower() and not 'thumbnail' in src.lower():
                return src
                
            # Check source elements
            for source in video.find_all('source'):
                src = source.get('src') or source.get('data-src')
                if src and '/video/' in src.lower() and not 'thumbnail' in src.lower():
                    return src
        
        # Try to find video URL in script tags
        for script in soup.find_all('script', type='application/json'):
            try:
                data = json.loads(script.string)
                if isinstance(data, dict):
                    # Look for video URLs in common Loom JSON structures
                    for key in ['url', 'videoUrl', 'video_url', 'hlsUrl', 'mp4Url']:
                        if key in data:
                            url = data[key]
                            if isinstance(url, str) and '/video/' in url.lower():
                                if not 'thumbnail' in url.lower():
                                    return url
            except:
                continue
        
        # Last resort: look for any video-like URLs in the page source
        video_patterns = [
            r'https?://[^"\']+?/video/[^"\']+'
        ]
        
        for pattern in video_patterns:
            matches = re.findall(pattern, page_source)
            for url in matches:
                if not 'thumbnail' in url.lower():
                    return url
        
        raise Exception("Could not find video URL in Loom page")
    except Exception as e:
        logger.error(f"Error extracting Loom video URL: {str(e)}")
        raise

def download_with_selenium(url: str, temp_dir: str) -> str:
    """Download video using Selenium for platforms that need browser interaction"""
    logger.info("Attempting to download with Selenium...")
    driver = None
    try:
        driver = setup_chrome_driver()
        driver.get(url)
        
        # Handle Loom videos specifically
        if 'loom.com' in url:
            video_url = extract_loom_video_url(driver, url)
            logger.info(f"Found Loom video URL: {video_url}")
        else:
            # Try multiple selectors for other platforms
            video_selectors = [
                "video",
                "video source",
                "iframe[src*='player']",
                ".video-player video",
                "#video-player",
                "[type='video/mp4']"
            ]
            
            video_url = None
            for selector in video_selectors:
                try:
                    element = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if selector == "iframe[src*='player']":
                        driver.switch_to.frame(element)
                        video_elements = driver.find_elements(By.TAG_NAME, "video")
                        if video_elements:
                            video_url = video_elements[0].get_attribute('src')
                        driver.switch_to.default_content()
                    else:
                        video_url = element.get_attribute('src')
                    
                    if video_url:
                        break
                except Exception as e:
                    logger.info(f"Selector {selector} failed: {str(e)}")
                    continue
        
        if not video_url:
            raise Exception("Could not find video source URL")
            
        logger.info(f"Attempting to download video from URL: {video_url}")
        
        # Download the video using requests
        timestamp = int(time.time())
        video_path = os.path.join(temp_dir, f"video_{timestamp}.mp4")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': url
        }
        
        response = requests.get(video_url, headers=headers, stream=True, timeout=30)
        response.raise_for_status()
        
        total_size = 0
        with open(video_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    total_size += len(chunk)
        
        logger.info(f"Downloaded video file size: {total_size} bytes")
        
        if total_size == 0:
            raise Exception("Downloaded file is empty")
            
        # Validate the video file
        try:
            with VideoFileClip(video_path) as video:
                if video.duration < 0.1:
                    raise Exception("Invalid video duration")
                if not video.audio:
                    raise Exception("No audio stream found in video")
        except Exception as e:
            raise Exception(f"Invalid video file: {str(e)}")
            
        return video_path
    except Exception as e:
        logger.error(f"Selenium download error: {str(e)}")
        raise
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

def download_with_requests(url: str, temp_dir: str) -> str:
    """Direct download using requests for simple video URLs"""
    logger.info("Attempting direct download with requests...")
    timestamp = int(time.time())
    video_path = os.path.join(temp_dir, f"video_{timestamp}.mp4")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    response = requests.get(url, headers=headers, stream=True)
    response.raise_for_status()
    
    with open(video_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    
    return video_path

def download_video(url: str) -> str:
    """Download video from URL using yt-dlp or direct download"""
    temp_dir = create_temp_dir()
    max_retries = 3
    last_error = None
    
    # Validate URL format
    try:
        parsed_url = urlparse(url)
        if not all([parsed_url.scheme, parsed_url.netloc]):
            raise Exception("Invalid URL format")
    except Exception as e:
        raise Exception(f"Invalid URL: {str(e)}")
    
    # Try to resolve domain first
    try:
        import socket
        domain = parsed_url.netloc.split(':')[0]
        socket.gethostbyname(domain)
    except socket.gaierror:
        raise Exception(f"Could not resolve domain: {domain}. Please check your internet connection and DNS settings.")
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Downloading video from {url} (attempt {attempt + 1}/{max_retries})")
            
            # Try yt-dlp first (works for most video platforms)
            try:
                timestamp = int(time.time())
                video_path = os.path.join(temp_dir, f"video_{timestamp}.mp4")
                ydl_opts = {
                    'format': 'bestvideo[ext=mp4][filesize<100M]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                    'outtmpl': video_path,
                    'quiet': True,
                    'no_warnings': True,
                    'socket_timeout': 60,  # Increased timeout
                    'retries': 5,          # Increased retries
                    'fragment_retries': 5,
                    'http_chunk_size': 5242880,  # 5MB chunks
                    'extractor_retries': 5,
                    'file_access_retries': 5,
                    'hls_prefer_native': True,
                    'external_downloader_args': ['--max-download-rate', '5M'],  # Reduced rate for stability
                    'noprogress': True,
                    'postprocessors': [{
                        'key': 'FFmpegVideoConvertor',
                        'preferedformat': 'mp4',
                    }],
                    'concurrent_fragments': 3,  # Parallel downloads
                    'buffersize': 32768,  # Increased buffer size
                    'http_headers': {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                        'Accept': '*/*',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Connection': 'keep-alive',
                    }
                }
                
                # Add specific options for YouTube
                if is_youtube_url(url):
                    ydl_opts.update({
                        'format': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best',
                        'youtube_include_dash_manifest': False,
                        'nocheckcertificate': True,
                        'extract_flat': False,
                        'force_generic_extractor': False,
                    })
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    logger.info("Attempting download with yt-dlp...")
                    ydl.download([url])
                    if os.path.exists(video_path) and os.path.getsize(video_path) > 0:
                        # Validate video file
                        try:
                            with VideoFileClip(video_path) as video:
                                if video.duration < 0.1:
                                    raise Exception("Invalid video duration")
                                if not video.audio:
                                    raise Exception("No audio stream found in video")
                            return video_path
                        except Exception as e:
                            logger.error(f"Invalid video file: {str(e)}")
                            if os.path.exists(video_path):
                                os.remove(video_path)
                            raise
            except Exception as e:
                logger.info(f"yt-dlp download failed: {str(e)}")
                last_error = e
            
            # Fallback: Try direct download for MP4/WebM URLs
            if re.search(r'\.(mp4|webm|mov)(\?.*)?$', url, re.I):
                try:
                    logger.info("Attempting direct download...")
                    timestamp = int(time.time())
                    video_path = os.path.join(temp_dir, f"video_{timestamp}.mp4")
                    
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                        'Accept': '*/*',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Connection': 'keep-alive',
                        'Range': 'bytes=0-'
                    }
                    
                    with requests.get(url, headers=headers, stream=True, timeout=60) as response:
                        response.raise_for_status()
                        with open(video_path, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                    
                    if os.path.exists(video_path) and os.path.getsize(video_path) > 0:
                        # Validate video file
                        try:
                            with VideoFileClip(video_path) as video:
                                if video.duration < 0.1:
                                    raise Exception("Invalid video duration")
                                if not video.audio:
                                    raise Exception("No audio stream found in video")
                            return video_path
                        except Exception as e:
                            logger.error(f"Invalid video file: {str(e)}")
                            if os.path.exists(video_path):
                                os.remove(video_path)
                            raise
                except Exception as e:
                    logger.info(f"Direct download failed: {str(e)}")
                    last_error = e
            
            # If both methods fail, try Selenium as last resort
            try:
                logger.info("Attempting download with Selenium...")
                return download_with_selenium(url, temp_dir)
            except Exception as e:
                logger.info(f"Selenium download failed: {str(e)}")
                last_error = e
            
            raise Exception(f"All download methods failed. Last error: {str(last_error)}")
            
        except Exception as e:
            logger.error(f"Error downloading video (attempt {attempt + 1}): {str(e)}")
            if attempt == max_retries - 1:
                raise Exception(f"Failed to download video after {max_retries} attempts: {str(e)}")
            time.sleep(2 ** attempt)  # Exponential backoff

def is_youtube_url(url: str) -> bool:
    """Check if URL is a YouTube URL"""
    parsed_url = urlparse(url)
    return parsed_url.hostname in ['www.youtube.com', 'youtube.com', 'youtu.be']

def is_loom_url(url: str) -> bool:
    """Check if URL is a Loom URL"""
    parsed_url = urlparse(url)
    return 'loom.com' in parsed_url.hostname if parsed_url.hostname else False

def extract_audio(video_path: str) -> str:
    """Extract audio from video file and return path to audio file"""
    try:
        logger.info(f"Extracting audio from {video_path}")
        
        if not os.path.exists(video_path):
            raise Exception(f"Video file not found: {video_path}")
            
        file_size = os.path.getsize(video_path)
        logger.info(f"Video file size: {file_size} bytes")
        
        if file_size == 0:
            raise Exception("Video file is empty")
            
        video = VideoFileClip(video_path)
        if video is None:
            raise Exception("Failed to load video file")
            
        if not video.audio:
            raise Exception("No audio stream found in video")
            
        # Create a temporary directory for the audio file
        temp_dir = create_temp_dir()
        audio_path = os.path.join(temp_dir, "audio.wav")
        
        # Disable audio playback during extraction
        video.audio.write_audiofile(audio_path, verbose=False, logger=None)
        video.close()
        
        if not os.path.exists(audio_path):
            raise Exception("Failed to create audio file")
            
        audio_size = os.path.getsize(audio_path)
        logger.info(f"Extracted audio file size: {audio_size} bytes")
        
        if audio_size == 0:
            raise Exception("Extracted audio file is empty")
            
        return audio_path
    except Exception as e:
        logger.error(f"Error extracting audio: {str(e)}")
        raise

def process_video(video_url: str) -> dict:
    """Process a video URL to extract audio, transcribe it, and generate action points"""
    temp_files = []
    try:
        logger.info("Step 1: Downloading video...")
        video_path = download_video(video_url)
        if not video_path:
            return {
                "status": "failed",
                "error": "Failed to download video",
                "transcription": None,
                "action_points": None
            }
        temp_files.append(video_path)

        logger.info("Step 2: Extracting audio...")
        audio_path = extract_audio(video_path)
        if not audio_path:
            return {
                "status": "failed",
                "error": "Failed to extract audio",
                "transcription": None,
                "action_points": None
            }
        temp_files.append(audio_path)

        logger.info("Step 3: Transcribing audio with Whisper...")
        transcription = transcribe_audio(audio_path)
        if not transcription:
            return {
                "status": "failed",
                "error": "Failed to transcribe audio",
                "transcription": None,
                "action_points": None
            }

        logger.info("Step 4: Extracting action points from transcription...")
        action_points = extract_action_points(transcription)
        if not action_points:
            return {
                "status": "failed",
                "error": "Failed to extract action points",
                "transcription": transcription,
                "action_points": None
            }

        return {
            "status": "completed",
            "error": None,
            "transcription": transcription,
            "action_points": json.dumps(action_points)  # Convert to JSON string for storage
        }

    except Exception as e:
        logger.error(f"Error in process_video: {str(e)}")
        return {
            "status": "failed",
            "error": str(e),
            "transcription": None,
            "action_points": None
        }
    finally:
        # Clean up temporary files
        for file_path in temp_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                # Try to remove parent temp directory if it's empty
                parent_dir = os.path.dirname(file_path)
                if os.path.exists(parent_dir) and not os.listdir(parent_dir):
                    os.rmdir(parent_dir)
            except Exception as e:
                logger.warning(f"Failed to clean up temporary file {file_path}: {str(e)}")

class VideoProcessor:
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
        
    def _is_s3_url(self, url: str) -> bool:
        """Check if the URL is an S3 URL."""
        parsed = urlparse(url)
        return parsed.netloc.endswith('amazonaws.com') and 's3' in parsed.netloc

    def _download_from_s3(self, url: str, output_path: str) -> bool:
        """Download video from S3 URL."""
        try:
            # First try with boto3 if available
            try:
                import boto3
                from urllib.parse import urlparse
                
                parsed_url = urlparse(url)
                bucket = parsed_url.netloc.split('.')[0]
                key = parsed_url.path.lstrip('/')
                
                # Try to get AWS credentials from environment variables
                aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
                aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
                aws_region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
                
                if aws_access_key_id and aws_secret_access_key:
                    s3 = boto3.client('s3',
                        aws_access_key_id=aws_access_key_id,
                        aws_secret_access_key=aws_secret_access_key,
                        region_name=aws_region
                    )
                else:
                    # Try to use default credentials
                    s3 = boto3.client('s3', region_name=aws_region)
                
                s3.download_file(bucket, key, output_path)
                return True
            except ImportError:
                logger.info("boto3 not available, falling back to direct download")
            except Exception as e:
                logger.warning(f"boto3 download failed: {str(e)}")
            
            # If boto3 fails or isn't available, try direct download with requests
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Accept': '*/*',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Range': 'bytes=0-'
                }
                
                # Add AWS credentials to headers if available
                if aws_access_key_id and aws_secret_access_key:
                    import hmac
                    import hashlib
                    from datetime import datetime
                    
                    # Generate AWS signature
                    date = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
                    amz_date = datetime.utcnow().strftime('%Y%m%d')
                    
                    canonical_request = f"GET\n{parsed_url.path}\n\nhost:{parsed_url.netloc}\n\nhost\nUNSIGNED-PAYLOAD"
                    string_to_sign = f"AWS4-HMAC-SHA256\n{date}\n{amz_date}/us-east-1/s3/aws4_request\n{hashlib.sha256(canonical_request.encode()).hexdigest()}"
                    
                    k_date = hmac.new(f'AWS4{aws_secret_access_key}'.encode(), amz_date.encode(), hashlib.sha256).digest()
                    k_region = hmac.new(k_date, b'us-east-1', hashlib.sha256).digest()
                    k_service = hmac.new(k_region, b's3', hashlib.sha256).digest()
                    k_signing = hmac.new(k_service, b'aws4_request', hashlib.sha256).digest()
                    signature = hmac.new(k_signing, string_to_sign.encode(), hashlib.sha256).hexdigest()
                    
                    authorization_header = f"AWS4-HMAC-SHA256 Credential={aws_access_key_id}/{amz_date}/us-east-1/s3/aws4_request, SignedHeaders=host, Signature={signature}"
                    headers['Authorization'] = authorization_header
                    headers['X-Amz-Date'] = date
                
                response = requests.get(url, headers=headers, stream=True, timeout=30)
                response.raise_for_status()
                
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                return True
            except requests.exceptions.RequestException as e:
                logger.warning(f"Direct S3 download failed: {str(e)}")
                
                # If direct download fails, try with yt-dlp as fallback
                ydl_opts = {
                    'format': 'best',
                    'outtmpl': output_path,
                    'quiet': True,
                    'no_warnings': True,
                    'extract_flat': False,
                    'nocheckcertificate': True,
                    'http_headers': headers,
                    'socket_timeout': 30,
                    'retries': 3,
                    'fragment_retries': 3,
                    'http_chunk_size': 10485760,  # 10MB
                    'extractor_retries': 3,
                    'file_access_retries': 3,
                    'hls_prefer_native': True,
                    'external_downloader_args': ['--max-download-rate', '10M']
                }
                
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([url])
                    return True
                except Exception as e:
                    logger.error(f"yt-dlp fallback failed: {str(e)}")
                    return False
                
        except Exception as e:
            logger.error(f"Error downloading from S3: {str(e)}")
            return False

    def download_video(self, url: str, max_attempts: int = 3) -> Optional[str]:
        """Download video from URL with support for S3."""
        logger.info(f"Step 1: Downloading video...")
        logger.info(f"Downloading video from {url} (attempt 1/{max_attempts})")
        
        # Create a unique filename
        video_id = str(hash(url))[-8:]
        output_path = os.path.join(self.temp_dir, f"video_{video_id}.mp4")
        
        # Handle S3 URLs differently
        if self._is_s3_url(url):
            logger.info("Detected S3 URL, using S3-specific download method")
            if self._download_from_s3(url, output_path):
                return output_path
            else:
                # If S3-specific method fails, fall back to regular yt-dlp
                logger.info("S3-specific download failed, falling back to yt-dlp")
                ydl_opts = {
                    'format': 'best',
                    'outtmpl': output_path,
                    'quiet': True,
                    'no_warnings': True,
                    'extract_flat': False,
                    'nocheckcertificate': True,
                    'socket_timeout': 30,
                    'retries': 3,
                    'fragment_retries': 3,
                    'http_chunk_size': 10485760,  # 10MB
                    'extractor_retries': 3,
                    'file_access_retries': 3,
                    'hls_prefer_native': True,
                    'external_downloader_args': ['--max-download-rate', '10M']
                }
                
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([url])
                    return output_path
                except Exception as e:
                    logger.error(f"Fallback download failed: {str(e)}")
                    return None
        else:
            # Use regular yt-dlp for non-S3 URLs
            logger.info("Attempting download with yt-dlp...")
            ydl_opts = {
                'format': 'best',
                'outtmpl': output_path,
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'nocheckcertificate': True,
                'socket_timeout': 30,
                'retries': 3,
                'fragment_retries': 3,
                'http_chunk_size': 10485760,  # 10MB
                'extractor_retries': 3,
                'file_access_retries': 3,
                'hls_prefer_native': True,
                'external_downloader_args': ['--max-download-rate', '10M']
            }
            
            for attempt in range(max_attempts):
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([url])
                    return output_path
                except Exception as e:
                    logger.error(f"Download attempt {attempt + 1} failed: {str(e)}")
                    if attempt < max_attempts - 1:
                        logger.info(f"Retrying download... (attempt {attempt + 2}/{max_attempts})")
                    else:
                        logger.error("All download attempts failed")
                        return None

    def extract_audio(self, video_path: str) -> Optional[str]:
        """Extract audio from video file."""
        logger.info("Step 2: Extracting audio...")
        logger.info(f"Extracting audio from {video_path}")
        
        # Get video file size
        video_size = os.path.getsize(video_path)
        logger.info(f"Video file size: {video_size} bytes")
        
        # Create output path for audio
        audio_path = os.path.join(self.temp_dir, f"audio_{os.path.basename(video_path)}.wav")
        
        try:
            # Use ffmpeg to extract audio
            cmd = [
                'ffmpeg', '-i', video_path,
                '-vn',  # No video
                '-acodec', 'pcm_s16le',  # PCM format
                '-ar', '16000',  # 16kHz sample rate
                '-ac', '1',  # Mono audio
                '-y',  # Overwrite output file
                audio_path
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)
            
            # Get audio file size
            audio_size = os.path.getsize(audio_path)
            logger.info(f"Extracted audio file size: {audio_size} bytes")
            
            return audio_path
        except subprocess.CalledProcessError as e:
            logger.error(f"Error extracting audio: {e.stderr.decode()}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error extracting audio: {str(e)}")
            return None

    def cleanup(self, video_path: str, audio_path: str) -> None:
        """Clean up temporary files."""
        try:
            if os.path.exists(video_path):
                os.remove(video_path)
            if os.path.exists(audio_path):
                os.remove(audio_path)
            logger.info("Cleaned up temporary files")
        except Exception as e:
            logger.error(f"Error cleaning up files: {str(e)}")

    def process_video(self, url: str) -> Dict[str, Any]:
        """Process video and return results."""
        video_path = None
        audio_path = None
        
        try:
            # Download video
            video_path = self.download_video(url)
            if not video_path:
                return {"error": "Failed to download video", "success": False}
            
            # Extract audio
            audio_path = self.extract_audio(video_path)
            if not audio_path:
                return {"error": "Failed to extract audio", "success": False}
            
            return {
                "video_path": video_path,
                "audio_path": audio_path,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error processing video: {str(e)}")
            return {"error": str(e), "success": False}
        finally:
            # Don't clean up files here - they'll be cleaned up after processing
            pass 
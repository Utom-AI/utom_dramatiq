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
import subprocess

# Configure logging to match organization's style
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
    
    response = requests.get(url, headers=headers, stream=True, timeout=30)
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

def download_video(url: str, temp_dir: str) -> str:
    """Download video from URL using appropriate method"""
    logger.info(f"Attempting to download video from URL: {url}")
    
    # Try yt-dlp first
    try:
        logger.info("Attempting download with yt-dlp...")
        timestamp = int(time.time())
        video_path = os.path.join(temp_dir, f"video_{timestamp}.mp4")
        
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': video_path,
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'socket_timeout': 60,
            'retries': 5,
            'fragment_retries': 5,
            'extractor_retries': 5,
            'file_access_retries': 5,
            'http_chunk_size': 5242880,  # 5MB chunks
            'concurrent_fragments': 3,
            'buffersize': 32768,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
        }
        
        # Special handling for YouTube
        if 'youtube.com' in url or 'youtu.be' in url:
            ydl_opts.update({
                'format': 'bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4][height<=1080]/best[ext=mp4]/best',
                'extract_flat': False,
                'force_generic_extractor': False
            })
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        # Validate the downloaded file
        if os.path.exists(video_path) and os.path.getsize(video_path) > 0:
            with VideoFileClip(video_path) as video:
                if video.duration > 0.1 and video.audio:
                    logger.info("Successfully downloaded video with yt-dlp")
                    return video_path
                else:
                    raise Exception("Invalid video file")
        else:
            raise Exception("Download failed or file is empty")
            
    except Exception as e:
        logger.warning(f"yt-dlp download failed: {str(e)}")
        
        # Try Selenium for platforms that need browser interaction
        try:
            logger.info("Attempting download with Selenium...")
            return download_with_selenium(url, temp_dir)
        except Exception as e:
            logger.warning(f"Selenium download failed: {str(e)}")
            
            # Try direct download as last resort
            try:
                logger.info("Attempting direct download...")
                return download_with_requests(url, temp_dir)
            except Exception as e:
                logger.error(f"All download methods failed: {str(e)}")
                raise

def extract_audio(video_path: str, temp_dir: str) -> str:
    """Extract audio from video file"""
    logger.info(f"Extracting audio from video: {video_path}")
    
    timestamp = int(time.time())
    audio_path = os.path.join(temp_dir, f"audio_{timestamp}.mp3")
    
    try:
        # Use ffmpeg to extract audio
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-vn',  # No video
            '-acodec', 'libmp3lame',  # Use MP3 codec
            '-ab', '192k',  # Bitrate
            '-ar', '44100',  # Sample rate
            '-y',  # Overwrite output file
            audio_path
        ]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"FFmpeg error: {stderr}")
            
        if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
            raise Exception("Audio extraction failed or file is empty")
            
        logger.info("Successfully extracted audio")
        return audio_path
        
    except Exception as e:
        logger.error(f"Error extracting audio: {str(e)}")
        raise

def cleanup(video_path: Optional[str] = None, audio_path: Optional[str] = None):
    """Clean up temporary files"""
    try:
        if video_path and os.path.exists(video_path):
            os.remove(video_path)
            logger.info(f"Removed video file: {video_path}")
            
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)
            logger.info(f"Removed audio file: {audio_path}")
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")

def process_video(video_url: str) -> Dict[str, Any]:
    """
    Download video and extract audio
    
    Args:
        video_url (str): URL of the video to process
        
    Returns:
        dict: Contains success status and paths to video and audio files
    """
    try:
        # Create temporary directory
        temp_dir = create_temp_dir()
        video_path = os.path.join(temp_dir, "video.mp4")
        audio_path = os.path.join(temp_dir, "audio.mp3")
        
        # Download video
        logger.info(f"Downloading video from {video_url}")
        response = requests.get(video_url, stream=True)
        response.raise_for_status()
        
        with open(video_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    
        # Extract audio
        logger.info("Extracting audio from video")
        video = VideoFileClip(video_path)
        video.audio.write_audiofile(audio_path)
        video.close()
        
        return {
            "success": True,
            "video_path": video_path,
            "audio_path": audio_path,
            "temp_dir": temp_dir
        }
        
    except Exception as e:
        logger.error(f"Error processing video: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def cleanup_files(video_path: str, audio_path: str):
    """
    Clean up temporary files
    
    Args:
        video_path (str): Path to video file
        audio_path (str): Path to audio file
    """
    try:
        # Get the directory containing the files
        temp_dir = os.path.dirname(video_path)
        
        # Remove files
        if os.path.exists(video_path):
            os.remove(video_path)
        if os.path.exists(audio_path):
            os.remove(audio_path)
            
        # Remove directory if empty
        if os.path.exists(temp_dir):
            os.rmdir(temp_dir)
            
    except Exception as e:
        logger.error(f"Error cleaning up files: {str(e)}") 
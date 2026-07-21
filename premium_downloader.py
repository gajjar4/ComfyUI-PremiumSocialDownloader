# premium_downloader.py
import os
import re
import hashlib
import json
import requests
import shutil
import subprocess
import wave
import numpy as np
import torch
import cv2
from PIL import Image
import yt_dlp
import folder_paths
import asyncio
from server import PromptServer
from aiohttp import web
from comfy.utils import ProgressBar

# --- Platform Detection Patterns ---
PLATFORM_PATTERNS = {
    'tiktok': [
        r'tiktok\.com/@[\w.-]+/video/\d+',
        r'tiktok\.com/[\w.-]+/video/\d+',
        r'vm\.tiktok\.com/[\w\d]+',
        r'vt\.tiktok\.com/[\w\d]+',
        r'm\.tiktok\.com/v/\d+',
        r'tiktok\.com/t/[\w\d]+',
    ],
    'twitter': [
        r'(twitter|x)\.com/[\w.-]+/status/\d+',
        r't\.co/[\w\d]+',
    ],
    'instagram': [
        r'instagram\.com/(?:[\w.-]+/)?(?:p|reel|reels|tv)/[\w-]+',
        r'instagr\.am/(?:p|reel|reels|tv)/[\w-]+',
        r'instagram\.com/share/[\w-]+',
    ],
    'youtube': [
        r'youtube\.com/watch\?[^ ]*v=[\w-]{11}',
        r'youtu\.be/[\w-]{11}',
        r'youtube\.com/(?:shorts|embed|live|v)/[\w-]{11}',
        r'youtube-nocookie\.com/embed/[\w-]{11}',
    ],
    'facebook': [
        r'fb\.watch/[\w-]+',
        r'facebook\.com/watch/?\?[^ ]*v=\d+',
        r'facebook\.com/[\w.-]+/videos/(?:[\w.-]+/)?\d+',
        r'facebook\.com/reel/\d+',
        r'facebook\.com/share/[vr]/[\w-]+',
        r'facebook\.com/(?:[\w.-]+/)?(?:video\.php|story\.php|permalink\.php)\?[^ ]*v?=?\d+',
    ]
}

COBALT_INSTANCES = [
    "https://co.otomir23.me/",
    "https://cobalt.tux.pizza/",
    "https://cobalt.moe/",
    "https://co.wuk.sh/"
]

def detect_platform(url: str) -> str:
    trimmed = url.strip()
    for platform, patterns in PLATFORM_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, trimmed, re.IGNORECASE):
                return platform
    return 'unknown'

# --- FFmpeg Finder ---
def get_ffmpeg_path():
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        return ffmpeg_path
    try:
        from imageio_ffmpeg import get_ffmpeg_exe
        ffmpeg_path = get_ffmpeg_exe()
        if ffmpeg_path and os.path.exists(ffmpeg_path):
            return ffmpeg_path
    except ImportError:
        pass
    for root, dirs, files in os.walk(os.path.join(os.path.abspath('.'), "custom_nodes")):
        for file in files:
            if file == "ffmpeg" or file == "ffmpeg.exe":
                fp = os.path.join(root, file)
                if os.path.exists(fp):
                    return fp
    return None

# --- Direct Download Helpers ---
def download_file(url, filepath):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    r = requests.get(url, headers=headers, stream=True, timeout=45)
    r.raise_for_status()
    with open(filepath, 'wb') as f:
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    return filepath

# --- API Fetchers ---
def fetch_tikwm(url):
    try:
        print(f"[PremiumDownloader] Querying Tikwm API for: {url}")
        resp = requests.post("https://www.tikwm.com/api/", data={"url": url}, timeout=15)
        if resp.status_code == 200:
            res_json = resp.json()
            if res_json.get("code") == 0:
                data = res_json.get("data", {})
                title = data.get("title", "TikTok Video")
                author = data.get("author", {}).get("nickname", "ASD")
                images = data.get("images", [])
                if images:
                    return {
                        "image_urls": images,
                        "title": title,
                        "author": author,
                        "platform": "tiktok"
                    }
                video_url = data.get("play") or data.get("hdplay")
                audio_url = data.get("music")
                return {
                    "video_url": video_url,
                    "audio_url": audio_url,
                    "title": title,
                    "author": author,
                    "platform": "tiktok"
                }
    except Exception as e:
        print(f"[PremiumDownloader] Tikwm API failed: {e}")
    return None

def fetch_vxtwitter(url):
    match = re.search(r'(?:twitter|x)\.com/([^/]+)/status/(\d+)', url)
    if not match:
        return None
    username, tweet_id = match.groups()
    api_url = f"https://api.vxtwitter.com/{username}/status/{tweet_id}"
    try:
        print(f"[PremiumDownloader] Querying vxTwitter API for tweet: {tweet_id}")
        resp = requests.get(api_url, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            media = data.get("media_extended", data.get("media", []))
            video_url = None
            image_urls = []
            for item in media:
                if item.get("type") in ("video", "gif"):
                    video_url = item.get("url")
                    break
                elif item.get("type") == "image":
                    image_urls.append(item.get("url"))
            title = data.get("text", f"Tweet by @{username}")
            author = data.get("user_name", username)
            return {
                "video_url": video_url,
                "image_urls": image_urls,
                "title": title,
                "author": author,
                "platform": "twitter"
            }
    except Exception as e:
        print(f"[PremiumDownloader] vxTwitter failed: {e}")
    return None

def fetch_cobalt(url, cobalt_api_url):
    try:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        payload = {
            "url": url,
            "videoQuality": "max",
            "filenameStyle": "basic"
        }
        base_url = cobalt_api_url.rstrip("/")
        try:
            resp = requests.post(base_url, json=payload, headers=headers, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") in ("tunnel", "redirect", "picker", "success"):
                    return parse_cobalt_response(data, url)
        except:
            pass
            
        try:
            resp = requests.post(f"{base_url}/api/json", json=payload, headers=headers, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") in ("tunnel", "redirect", "picker", "success"):
                    return parse_cobalt_response(data, url)
        except:
            pass
    except Exception as e:
        print(f"[PremiumDownloader] Cobalt failed: {e}")
    return None

def parse_cobalt_response(data, url):
    status = data.get("status")
    platform = detect_platform(url)
    title = data.get("filename", "video").split(".")[0]
    if status in ("tunnel", "redirect", "success"):
        return {
            "video_url": data.get("url"),
            "title": title,
            "author": "ASD",
            "platform": platform
        }
    elif status == "picker":
        items = data.get("picker", [])
        videos = [item for item in items if item.get("type") == "video"]
        photos = [item for item in items if item.get("type") in ("photo", "image")]
        if videos:
            return {
                "video_url": videos[0].get("url"),
                "title": title,
                "author": "ASD",
                "platform": platform
            }
        elif photos:
            return {
                "image_urls": [photo.get("url") for photo in photos],
                "title": title,
                "author": "ASD",
                "platform": platform
            }
    return None

def fetch_cobalt_pool(url):
    for api_url in COBALT_INSTANCES:
        try:
            print(f"[PremiumDownloader] Trying Cobalt Pool instance: {api_url}")
            res = fetch_cobalt(url, api_url)
            if res:
                return res
        except Exception as e:
            print(f"[PremiumDownloader] Cobalt Pool instance {api_url} failed: {e}")
    return None

# --- yt-dlp Extractor ---
def fetch_ytdlp(url, output_dir, file_id):
    print(f"[PremiumDownloader] Attempting download with local yt-dlp: {url}")
    out_tmpl = os.path.join(output_dir, f"{file_id}.%(ext)s")
    ydl_opts = {
        'format': 'bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/best',
        'outtmpl': out_tmpl,
        'quiet': True,
        'no_warnings': True,
        'no_check_certificate': True,
        'merge_output_format': 'mp4',
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            base_path = os.path.splitext(filename)[0]
            for ext in ('.mp4', '.mkv', '.webm', '.avi'):
                check_path = base_path + ext
                if os.path.exists(check_path):
                    return check_path, info
            if os.path.exists(filename):
                return filename, info
            for f in os.listdir(output_dir):
                if f.startswith(file_id):
                    return os.path.join(output_dir, f), info
    except Exception as e:
        print(f"[PremiumDownloader] yt-dlp failed: {e}")
    return None, None

# --- Audio Extractor using FFmpeg ---
def extract_audio(video_path, audio_path, ffmpeg_bin, start_time=0.0, duration=0.0):
    if not ffmpeg_bin:
        return False
    print(f"[PremiumDownloader] Extracting audio to wav: {audio_path}")
    try:
        cmd = [ffmpeg_bin, "-y"]
        if start_time > 0.0:
            cmd += ["-ss", str(start_time)]
        cmd += ["-i", video_path]
        if duration > 0.0:
            cmd += ["-t", str(duration)]
        cmd += [
            "-vn", "-acodec", "pcm_s16le",
            "-ar", "44100", "-ac", "2",
            audio_path
        ]
        res = subprocess.run(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20)
        if res.returncode == 0 and os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
            return True
    except Exception as e:
        print(f"[PremiumDownloader] Audio extraction failed: {e}")
    return False

# --- WAV Audio Loader ---
def load_audio_wav(wav_path):
    if not wav_path or not os.path.exists(wav_path):
        return None
    try:
        with wave.open(wav_path, 'rb') as w:
            params = w.getparams()
            channels, sampwidth, framerate, nframes = params[:4]
            data = w.readframes(nframes)
            if sampwidth == 2:
                audio_data = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
            elif sampwidth == 1:
                audio_data = (np.frombuffer(data, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
            elif sampwidth == 4:
                audio_data = np.frombuffer(data, dtype=np.int32).astype(np.float32) / 2147483648.0
            else:
                return None
            audio_tensor = torch.from_numpy(audio_data)
            audio_tensor = audio_tensor.reshape((-1, channels)).transpose(0, 1).unsqueeze(0)
            return {"waveform": audio_tensor, "sample_rate": framerate}
    except Exception as e:
        print(f"[PremiumDownloader] Failed to load WAV audio: {e}")
    return None

# --- WebP Generator ---
def generate_webp_preview(video_path, url_hash, out_fps=29.97):
    try:
        temp_dir = folder_paths.get_temp_directory()
        preview_name = f"{url_hash}_preview.webp"
        preview_path = os.path.join(temp_dir, preview_name)
        if os.path.exists(preview_path):
            return preview_name
            
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return ""
        frames = []
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frames.append(frame_rgb)
            if len(frames) >= 120:
                break
        cap.release()
        
        if not frames:
            return ""
            
        preview_frames = []
        step = max(1, len(frames) // 12)
        for idx in range(0, len(frames), step):
            frame_np = frames[idx]
            ph, pw, _ = frame_np.shape
            plimit = 320
            if pw > plimit or ph > plimit:
                if pw > ph:
                    tpw = plimit
                    tph = int(plimit * (ph / pw))
                else:
                    tph = plimit
                    tpw = int(plimit * (pw / ph))
                frame_np = cv2.resize(frame_np, (tpw, tph), interpolation=cv2.INTER_AREA)
            preview_frames.append(Image.fromarray(frame_np))
            
        if preview_frames:
            preview_frames[0].save(
                preview_path,
                save_all=True,
                append_images=preview_frames[1:],
                duration=int(max(50, (1000 / out_fps) * step)),
                loop=0
            )
            return preview_name
    except Exception as e:
        print(f"[PremiumDownloader] Failed to generate preview WebP: {e}")
    return ""

# --- API Download Handler Helper ---
def download_helper(url, max_resolution, custom_download_path=""):
    url = url.strip()
    url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
    
    # Process custom download path if provided
    if custom_download_path and custom_download_path.strip():
        downloader_dir = custom_download_path.strip()
        os.makedirs(downloader_dir, exist_ok=True)
    else:
        input_dir = folder_paths.get_input_directory()
        downloader_dir = os.path.join(input_dir, "social_downloads")
        os.makedirs(downloader_dir, exist_ok=True)
    
    video_output = os.path.join(downloader_dir, f"{url_hash}.mp4")
    # Cache audio files by start/duration to prevent extraction latency
    audio_output = os.path.join(downloader_dir, f"{url_hash}_trimmed_0.0_0.0.wav")
    images_dir = os.path.join(downloader_dir, f"{url_hash}_images")
    
    platform = detect_platform(url)
    ffmpeg_bin = get_ffmpeg_path()
    
    meta_title = "Social Media Content"
    meta_author = "ASD"
    is_images_carousel = False
    
    # Check cache
    cache_hit = False
    if os.path.exists(video_output) and os.path.getsize(video_output) > 0:
        cache_hit = True
    elif os.path.exists(images_dir) and os.path.isdir(images_dir) and len(os.listdir(images_dir)) > 0:
        is_images_carousel = True
        cache_hit = True
        
    if not cache_hit:
        meta = None
        if platform == 'tiktok':
            meta = fetch_tikwm(url)
            if not meta:
                meta = fetch_cobalt_pool(url)
        elif platform == 'twitter':
            meta = fetch_vxtwitter(url)
            if not meta:
                meta = fetch_cobalt_pool(url)
        else:
            meta = fetch_cobalt_pool(url)
            
        if meta:
            meta_title = meta.get("title", meta_title)
            meta_author = meta.get("author", meta_author)
            
            if meta.get("image_urls"):
                os.makedirs(images_dir, exist_ok=True)
                for i, img_url in enumerate(meta["image_urls"]):
                    img_path = os.path.join(images_dir, f"img_{i:04d}.jpg")
                    try:
                        download_file(img_url, img_path)
                    except Exception as e:
                        print(f"[PremiumDownloader] Image Carousel download failed for frame {i}: {e}")
                is_images_carousel = True
            elif meta.get("video_url"):
                try:
                    download_file(meta["video_url"], video_output)
                except:
                    meta = None
                    
        if not os.path.exists(video_output) and not is_images_carousel:
            dl_path, dl_info = fetch_ytdlp(url, downloader_dir, url_hash)
            if dl_path and os.path.exists(dl_path):
                if dl_path != video_output:
                    shutil.move(dl_path, video_output)
                if dl_info:
                    meta_title = dl_info.get("title", meta_title)
                    meta_author = dl_info.get("uploader", meta_author)
            else:
                return None
                
    # Extract audio (base helper)
    has_audio = False
    if not is_images_carousel:
        if not os.path.exists(audio_output):
            extract_audio(video_output, audio_output, ffmpeg_bin)
        if os.path.exists(audio_output) and os.path.getsize(audio_output) > 0:
            has_audio = True
            
    out_width = 720
    out_height = 1280
    out_fps = 29.97
    out_duration = 10.0
    
    if is_images_carousel:
        image_files = [f for f in os.listdir(images_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
        if image_files:
            img = Image.open(os.path.join(images_dir, image_files[0]))
            out_width, out_height = img.size
            out_fps = 1.0
            out_duration = float(len(image_files))
    else:
        cap = cv2.VideoCapture(video_output)
        if cap.isOpened():
            out_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            out_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = float(cap.get(cv2.CAP_PROP_FPS))
            if fps > 0:
                out_fps = fps
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            out_duration = total_frames / out_fps
            cap.release()
            
    preview_name = generate_webp_preview(video_output, url_hash, out_fps) if not is_images_carousel else ""
    
    # Copy files to standard input folder if using custom path
    if custom_download_path and custom_download_path.strip():
        default_dir = os.path.join(folder_paths.get_input_directory(), "social_downloads")
        os.makedirs(default_dir, exist_ok=True)
        
        default_video = os.path.join(default_dir, f"{url_hash}.mp4")
        if os.path.exists(video_output) and not os.path.exists(default_video):
            try: shutil.copy2(video_output, default_video)
            except Exception as e: print(f"[PremiumDownloader] Copy to default preview failed: {e}")
            
        default_audio = os.path.join(default_dir, f"{url_hash}_trimmed_0.0_0.0.wav")
        if os.path.exists(audio_output) and not os.path.exists(default_audio):
            try: shutil.copy2(audio_output, default_audio)
            except Exception as e: print(f"[PremiumDownloader] Copy to default preview failed: {e}")
            
        if is_images_carousel and os.path.exists(images_dir):
            default_images = os.path.join(default_dir, f"{url_hash}_images")
            if not os.path.exists(default_images):
                try: shutil.copytree(images_dir, default_images)
                except Exception as e: print(f"[PremiumDownloader] Copy to default preview failed: {e}")

    return {
        "url": url,
        "hash": url_hash,
        "filename": f"{url_hash}.mp4" if not is_images_carousel else "",
        "video_path": video_output,
        "audio_path": audio_output if has_audio else "",
        "title": meta_title,
        "author": meta_author,
        "platform": platform,
        "width": out_width,
        "height": out_height,
        "fps": out_fps,
        "duration": out_duration,
        "is_images_carousel": is_images_carousel,
        "preview_name": preview_name
    }

# --- Register server API handlers ---
@PromptServer.instance.routes.post("/premium_downloader/download")
async def api_download(request):
    try:
        data = await request.json()
        url = data.get("url")
        max_res = data.get("max_resolution", "720")
        custom_path = data.get("custom_download_path", "")
        
        if not url:
            return web.json_response({"success": False, "error": "No URL provided"})
            
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, download_helper, url, max_res, custom_path)
        
        if result:
            return web.json_response({"success": True, "data": result})
        else:
            return web.json_response({"success": False, "error": "All download options failed"})
    except Exception as e:
        return web.json_response({"success": False, "error": str(e)})


# --- Main Premium ComfyUI Node Class ---
class PremiumSocialMediaDownloaderNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "url": ("STRING", {"multiline": False, "default": ""}),
                "max_resolution": (["Original", "1080", "720", "512", "384", "256"], {"default": "720"}),
                "start_time": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 10000.0, "step": 0.1}),
                "duration": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 10000.0, "step": 0.1}),
                "frame_load_cap": ("INT", {"default": 128, "min": 0, "max": 100000, "step": 1}),
                "select_every_nth": ("INT", {"default": 1, "min": 1, "step": 1}),
                "force_redownload": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                "custom_download_path": ("STRING", {"default": ""}),
            },
            "hidden": {
                "playlist_data": "STRING",
                "unique_id": "UNIQUE_ID"
            }
        }

    RETURN_TYPES = ("IMAGE", "AUDIO", "STRING", "STRING", "FLOAT", "INT", "INT", "INT", "FLOAT", "STRING")
    RETURN_NAMES = ("IMAGE", "AUDIO", "video_path", "audio_path", "fps", "width", "height", "frame_count", "duration", "metadata_text")
    FUNCTION = "download_and_load"
    CATEGORY = "social_downloader"
    OUTPUT_NODE = True

    def download_and_load(self, url, max_resolution="720", start_time=0.0, duration=0.0,
                          frame_load_cap=128, select_every_nth=1, force_redownload=False,
                          custom_download_path="", playlist_data="", unique_id=None):
                          
        # Initialize default values
        custom_width = 0
        custom_height = 0
        is_images_carousel = False
        meta_title = "Social Media Content"
        meta_author = "ASD"
        
        # Check if playlist_data is active and has a selected index
        selected_video = None
        if playlist_data:
            try:
                p_data = json.loads(playlist_data)
                downloaded = p_data.get("downloaded_videos", [])
                selected_idx = p_data.get("selected_index", 0)
                if downloaded and 0 <= selected_idx < len(downloaded):
                    selected_video = downloaded[selected_idx]
                    print(f"[PremiumDownloader] Selected playlist item: {selected_video['title']}")
            except Exception as e:
                print(f"[PremiumDownloader] Playlist parsing failed: {e}")
                
        # If playlist item is selected, override inputs (uses absolute cached paths)
        if selected_video:
            url = selected_video["url"]
            platform = selected_video["platform"]
            video_output = selected_video["video_path"]
            url_hash = selected_video["hash"]
            downloader_dir = os.path.dirname(video_output)
            audio_output = os.path.join(downloader_dir, f"{url_hash}_trimmed_{start_time}_{duration}.wav")
            meta_title = selected_video["title"]
            meta_author = selected_video["author"]
            is_images_carousel = selected_video.get("is_images_carousel", False)
            images_dir = os.path.join(downloader_dir, f"{url_hash}_images")
        else:
            url = url.strip()
            url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
            
            # Setup output folder path (dynamic custom override)
            if custom_download_path and custom_download_path.strip():
                downloader_dir = custom_download_path.strip()
                os.makedirs(downloader_dir, exist_ok=True)
            else:
                input_dir = folder_paths.get_input_directory()
                downloader_dir = os.path.join(input_dir, "social_downloads")
                os.makedirs(downloader_dir, exist_ok=True)
                
            video_output = os.path.join(downloader_dir, f"{url_hash}.mp4")
            audio_output = os.path.join(downloader_dir, f"{url_hash}_trimmed_{start_time}_{duration}.wav")
            images_dir = os.path.join(downloader_dir, f"{url_hash}_images")
            platform = detect_platform(url)
            
            # Normal Cache checks
            cache_hit = False
            if not force_redownload:
                if os.path.exists(video_output) and os.path.getsize(video_output) > 0:
                    cache_hit = True
                elif os.path.exists(images_dir) and os.path.isdir(images_dir) and len(os.listdir(images_dir)) > 0:
                    is_images_carousel = True
                    cache_hit = True
                    
            if not cache_hit:
                if os.path.exists(video_output):
                    os.remove(video_output)
                if os.path.exists(audio_output):
                    os.remove(audio_output)
                if os.path.exists(images_dir):
                    shutil.rmtree(images_dir, ignore_errors=True)
                    
                meta = None
                if platform == 'tiktok':
                    meta = fetch_tikwm(url)
                    if not meta:
                        meta = fetch_cobalt_pool(url)
                elif platform == 'twitter':
                    meta = fetch_vxtwitter(url)
                    if not meta:
                        meta = fetch_cobalt_pool(url)
                else:
                    meta = fetch_cobalt_pool(url)
                    
                if meta:
                    meta_title = meta.get("title", meta_title)
                    meta_author = meta.get("author", meta_author)
                    if meta.get("image_urls"):
                        os.makedirs(images_dir, exist_ok=True)
                        for i, img_url in enumerate(meta["image_urls"]):
                            img_path = os.path.join(images_dir, f"img_{i:04d}.jpg")
                            try:
                                download_file(img_url, img_path)
                            except Exception as e:
                                print(f"[PremiumDownloader] Image Carousel download failed for frame {i}: {e}")
                        is_images_carousel = True
                    elif meta.get("video_url"):
                        try:
                            download_file(meta["video_url"], video_output)
                        except:
                            meta = None
                            
                if not os.path.exists(video_output) and not is_images_carousel:
                    dl_path, dl_info = fetch_ytdlp(url, downloader_dir, url_hash)
                    if dl_path and os.path.exists(dl_path):
                        if dl_path != video_output:
                            shutil.move(dl_path, video_output)
                        if dl_info:
                            meta_title = dl_info.get("title", meta_title)
                            meta_author = dl_info.get("uploader", meta_author)
                    else:
                        raise RuntimeError("[PremiumDownloader] All download methods failed.")
                        
        # Setup audio extraction with dynamic crop trim (Now properly cached to prevent latency!)
        ffmpeg_bin = get_ffmpeg_path()
        has_audio = False
        if not is_images_carousel:
            if not os.path.exists(audio_output) or force_redownload:
                if os.path.exists(audio_output):
                    try: os.remove(audio_output)
                    except: pass
                extract_audio(video_output, audio_output, ffmpeg_bin, start_time, duration)
            if os.path.exists(audio_output) and os.path.getsize(audio_output) > 0:
                has_audio = True
                
        # --- LOADING MEDIA INTO TENSORS ---
        out_fps = 0.0
        out_width = 0
        out_height = 0
        out_duration = 0.0
        
        if is_images_carousel:
            image_files = sorted([f for f in os.listdir(images_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))])
            if not image_files:
                raise RuntimeError("[PremiumDownloader] Carousel folder empty.")
                
            np_frames_list = []
            for img_name in image_files:
                img_path = os.path.join(images_dir, img_name)
                try:
                    pil_img = Image.open(img_path).convert("RGB")
                    w, h = pil_img.size
                    target_w, target_h = custom_width, custom_height
                    if target_w == 0 and target_h == 0 and max_resolution != "Original":
                        limit = int(max_resolution)
                        if w > limit or h > limit:
                            if w > h:
                                target_w = limit
                                target_h = int(limit * (h / w))
                            else:
                                target_h = limit
                                target_w = int(limit * (w / h))
                    if target_w > 0 or target_h > 0:
                        if target_w == 0:
                            target_w = int(target_h * (w / h))
                        elif target_h == 0:
                            target_h = int(target_w * (h / w))
                        pil_img = pil_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
                        w, h = target_w, target_h
                        
                    np_frames_list.append(np.array(pil_img))
                    out_width, out_height = w, h
                except:
                    pass
            
            # Vectorized Fast Tensor Conversion
            np_frames = np.stack(np_frames_list, axis=0)
            images_tensor = torch.from_numpy(np_frames).float() / 255.0
            out_fps = 1.0
            out_duration = float(len(np_frames_list))
            audio_dict = None
            audio_output_path = ""
            video_output_path = ""
            total_loaded_frames = len(np_frames_list)
            
        else:
            # Get video metadata
            cap = cv2.VideoCapture(video_output)
            if not cap.isOpened():
                raise RuntimeError(f"[PremiumDownloader] Failed to open video: {video_output}")
                
            src_fps = float(cap.get(cv2.CAP_PROP_FPS))
            src_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            src_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            src_total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            cap.release()
            
            if src_total_frames <= 0:
                src_total_frames = 1
            out_fps = src_fps if src_fps > 0 else 29.97
            
            start_frame = 0
            if start_time > 0.0:
                start_frame = int(start_time * src_fps)
                
            max_to_load = frame_load_cap
            if duration > 0.0:
                duration_frames = int(duration * src_fps)
                if max_to_load > 0:
                    max_to_load = min(max_to_load, duration_frames)
                else:
                    max_to_load = duration_frames
            
            total_to_load = max_to_load if max_to_load > 0 else src_total_frames
            
            # Setup dynamic custom dimensions based on resolution choice
            target_w, target_h = custom_width, custom_height
            if target_w == 0 and target_h == 0 and max_resolution != "Original":
                limit = int(max_resolution)
                if src_width > limit or src_height > limit:
                    if src_width > src_height:
                        target_w = limit
                        target_h = int(limit * (src_height / src_width))
                    else:
                        target_h = limit
                        target_w = int(limit * (src_width / src_height))
                        
            if target_w > 0 or target_h > 0:
                if target_w == 0:
                    target_w = int(target_h * (src_width / src_height))
                elif target_h == 0:
                    target_h = int(target_w * (src_height / src_width))
                target_w = (target_w // 2) * 2
                target_h = (target_h // 2) * 2
                out_width, out_height = target_w, target_h
            else:
                out_width, out_height = src_width, src_height
                
            pbar = ProgressBar(total_to_load)
            
            # --- MEMORY WIZARDRY PIPELINE: Generator with in-place division ---
            def frame_generator(video_path, start, max_load, skip_nth, tw, th, pb, ttl):
                video_cap = cv2.VideoCapture(video_path)
                if not video_cap.isOpened():
                    return
                if start > 0:
                    video_cap.set(cv2.CAP_PROP_POS_FRAMES, start)
                    
                frame_idx = start
                total_read = 0
                
                while True:
                    # Speed Optimization: Grab the frame without decoding first!
                    ret = video_cap.grab()
                    if not ret:
                        break
                        
                    if (frame_idx - start) % skip_nth == 0:
                        ret, frame = video_cap.retrieve()
                        if not ret:
                            break
                            
                        # Micro-Optimization: Resize the raw BGR frame first (much faster than RGB!)
                        if tw > 0 or th > 0:
                            frame = cv2.resize(frame, (tw, th), interpolation=cv2.INTER_AREA)
                            
                        # Convert to RGB on the smaller resized frame
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        
                        # In-place C++ tensor division (No memory copies!)
                        frame_float = np.array(frame_rgb, dtype=np.float32)
                        torch.from_numpy(frame_float).div_(255.0)
                        
                        yield frame_float
                        total_read += 1
                        
                        if pb:
                            pb.update_absolute(total_read, ttl)
                            
                        if max_load > 0 and total_read >= max_load:
                            break
                            
                    frame_idx += 1
                video_cap.release()
                
            gen = frame_generator(video_output, start_frame, max_to_load, select_every_nth, target_w, target_h, pbar, total_to_load)
            
            # np.fromiter reads from the generator directly into a single stacked continuous memory array
            np_frames = np.fromiter(gen, np.dtype((np.float32, (out_height, out_width, 3))))
            
            if len(np_frames) == 0:
                raise RuntimeError("[PremiumDownloader] Frame decoder returned empty output.")
                
            images_tensor = torch.from_numpy(np_frames)
            out_fps = src_fps / select_every_nth
            out_duration = len(np_frames) / out_fps
            audio_dict = load_audio_wav(audio_output) if has_audio else None
            audio_output_path = audio_output if has_audio else ""
            video_output_path = video_output
            total_loaded_frames = len(np_frames)
            
        # Copy output to default preview dir if using custom path in main execution
        if custom_download_path and custom_download_path.strip():
            default_dir = os.path.join(folder_paths.get_input_directory(), "social_downloads")
            os.makedirs(default_dir, exist_ok=True)
            
            default_video = os.path.join(default_dir, f"{url_hash}.mp4")
            if os.path.exists(video_output_path) and not os.path.exists(default_video):
                try: shutil.copy2(video_output_path, default_video)
                except Exception as e: print(f"[PremiumDownloader] Copy to default preview failed: {e}")
                
            default_audio = os.path.join(default_dir, f"{url_hash}_trimmed_{start_time}_{duration}.wav")
            if os.path.exists(audio_output_path) and not os.path.exists(default_audio):
                try: shutil.copy2(audio_output_path, default_audio)
                except Exception as e: print(f"[PremiumDownloader] Copy to default preview failed: {e}")
                
            if is_images_carousel and os.path.exists(images_dir):
                default_images = os.path.join(default_dir, f"{url_hash}_images")
                if not os.path.exists(default_images):
                    try: shutil.copytree(images_dir, default_images)
                    except Exception as e: print(f"[PremiumDownloader] Copy to default preview failed: {e}")
                    
        # Metadata Formatter
        meta_str = (
            f"=== Premium Social Downloader ===\n"
            f"Platform: {platform.upper()}\n"
            f"Title: {meta_title}\n"
            f"Author: {meta_author}\n"
            f"Resolution: {out_width}x{out_height}\n"
            f"FPS: {out_fps:.2f}\n"
            f"Frames: {total_loaded_frames}\n"
            f"Duration: {out_duration:.2f}s\n"
            f"Video Path: {video_output_path}\n"
            f"Audio Path: {audio_output_path}\n"
        )
        
        # --- UI Outputs (Pass details to custom DOM widget) ---
        ui_video = []
        if not is_images_carousel and video_output_path:
            ui_video = [{
                "filename": f"{url_hash}.mp4",
                "subfolder": "social_downloads",
                "type": "input",
                "title": meta_title,
                "author": meta_author,
                "platform": platform,
                "width": out_width,
                "height": out_height
            }]
            
        return {
            "ui": {
                "video": ui_video
            },
            "result": (
                images_tensor,
                audio_dict,
                video_output_path,
                audio_output_path,
                float(out_fps),
                int(out_width),
                int(out_height),
                total_loaded_frames,
                float(out_duration),
                meta_str
            )
        }

    @classmethod
    def IS_CHANGED(cls, url, max_resolution="720", start_time=0.0, duration=0.0,
                   frame_load_cap=128, select_every_nth=1, force_redownload=False,
                   custom_download_path="", playlist_data="", unique_id=None):
        hash_str = f"{url}_{max_resolution}_{start_time}_{duration}_{frame_load_cap}_{select_every_nth}_{force_redownload}_{custom_download_path}_{playlist_data}"
        return hashlib.md5(hash_str.encode('utf-8')).hexdigest()

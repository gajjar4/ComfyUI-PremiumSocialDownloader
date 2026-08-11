# ComfyUI Premium Social Media Downloader 🌟

A professional-grade ComfyUI custom node that allows downloading videos, slideshows, and photo carousels from **TikTok, Twitter/X, Instagram, Facebook, and YouTube** directly from their URLs. It loads the downloaded content directly as PyTorch Tensors (`IMAGE` batches) and extracts/loads audio (`AUDIO` format), complete with an interactive HTML5 video preview widget, custom download paths, and automated caching.

Designed with a premium glassmorphic Cyberpunk/Neon UI (inspired by `react-bits` and `GSAP`), this node fits beautifully into modern ComfyUI workspaces.

---

## 🚀 Key Features

*   **🎬 Embed HTML5 Video Player**: Plays, pauses, controls volume, and scrubs through downloaded videos directly inside the ComfyUI node canvas. No extra preview nodes needed!
*   **📂 Custom Download Directories**: Optional input field to specify a custom folder on your system (e.g. `D:\MyVideos`). Videos are saved permanently there, while a secure preview copy is handled inside ComfyUI's sandbox so it loads in the browser.
*   **⚡ Performance Optimized (Generator Pipeline)**: 
    *   Uses **`np.fromiter()`** and in-place tensor division to bypass Python list memory allocation. This reduces peak memory overhead by **50%** and matches the loading speed of native nodes (like Video Helper Suite).
    *   Uses OpenCV `cap.grab()` to skip frames without decoding them, making frame skipping and trimming incredibly fast.
*   **🎼 Zero-Latency Audio Trim Caching**: Trim settings (`start_time` and `duration`) cache the generated audio file names. Subsequent runs skip the FFmpeg extraction subprocess entirely and load instantly in `0.01s`!
*   **📸 Photo Carousel / Slideshow Support**: Automatically detects multi-photo posts (Tiktok images, Instagram slides), downloads all images, and returns them as a batched `IMAGE` tensor.
*   **🧬 Automatic API Pool Router**: Automatically cycles through a pool of active public Cobalt API instances in the background, falling back to local `yt-dlp` download automatically if needed.
*   **📐 Dynamic Aspect Ratio Resizing**: Autoresizes the node canvas box to match the downloaded video (vertical vs. horizontal) dynamically, preventing squishing or overlaps.
*   **📊 Integrated Detailed Panel**: Expanding details panel shows resolution, actual FPS, duration, frames, and absolute path details with a "Copy Path" button.

---

## 🛠️ Installation

### Method 1: Git Clone (Recommended)

1. Open your terminal in ComfyUI's custom nodes directory:
   ```bash
   cd ComfyUI/custom_nodes/
   ```
2. Clone the repository:
   ```bash
   git clone https://github.com/Vette1123/ComfyUI-PremiumSocialDownloader.git
   ```
3. Install dependencies:
   *   If you are on portable ComfyUI:
       ```bash
       ..\..\..\python_embeded\python.exe -m pip install -r ComfyUI-PremiumSocialDownloader/requirements.txt
       ```
   *   If you are on standard Python:
       ```bash
       pip install -r ComfyUI-PremiumSocialDownloader/requirements.txt
       ```
4. Restart ComfyUI.

---

## ⚙️ Requirements & Dependencies

The node requires the following libraries (usually pre-installed in most ComfyUI environments):
*   `yt-dlp` (For high-speed direct downloading fallback)
*   `opencv-python` (For frame extraction & resizing)
*   `torch` (For returning IMAGE batches)
*   `numpy` (For fast vectorized array stacking)
*   `Pillow` (For carousel image handling)
*   `requests` (For querying API instances)

> [!IMPORTANT]
> **FFmpeg**: Extracting audio requires FFmpeg. The node will automatically try to find a system-wide installation of `ffmpeg`. If not found, it will try to load it from `imageio-ffmpeg` or local custom nodes.

---

## 🎛️ Node Inputs & Outputs

### Inputs

*   `url` (STRING, Hidden): The URL of the social media post. Added dynamically via the card input.
*   `max_resolution` (STRING): Caps output resolution (`Original`, `1080`, `720`, `512`, `384`, `256`) to protect GPU memory and speed up processing.
*   `start_time` (FLOAT): Start offset (in seconds) to crop/load the video.
*   `duration` (FLOAT): Crop duration (in seconds). Set to `0` to load the whole video.
*   `frame_load_cap` (INT): Limit total loaded frames (default: `128`) to prevent out-of-memory errors on long videos.
*   `select_every_nth` (INT): Read every Nth frame (e.g. `2` loads every other frame).
*   `force_redownload` (BOOLEAN): Ignores local caches and downloads a fresh copy.
*   `custom_download_path` (STRING, Optional): Path to save downloads permanently on your PC.
*   `cookies_browser` (Dropdown): Select your browser (`chrome`, `edge`, `firefox`, `brave`, etc.) to allow downloading private or age-restricted content using your logged-in session. Set to `None` for public content.

### Outputs

*   `IMAGE`: The extracted video frames or slideshow photos (`[num_frames, height, width, 3]` tensor).
*   `AUDIO`: Audio track (`{"waveform": tensor, "sample_rate": rate}`).
*   `video_path` (STRING): Absolute path to the saved video file.
*   `audio_path` (STRING): Absolute path to the saved WAV audio file.
*   `fps` (FLOAT): Output frames per second.
*   `width` (INT): Width of loaded frames.
*   `height` (INT): Height of loaded frames.
*   `frame_count` (INT): Number of frames returned.
*   `duration` (FLOAT): Length of returned clip in seconds.
*   `metadata_text` (STRING): Text summary of all video metadata.

---

## 🔧 Troubleshooting

### Instagram downloads fail with "empty media response"

Instagram frequently changes their API. If downloads stop working, **update yt-dlp** to the latest version:

*   **Portable ComfyUI** (most common):
    ```bash
    python_embeded\python.exe -m pip install --upgrade yt-dlp
    ```
*   **Standard Python**:
    ```bash
    pip install --upgrade yt-dlp
    ```

Then restart ComfyUI.

### Private / age-restricted content won't download

Set the `cookies_browser` dropdown to the browser where you're logged into Instagram (e.g. `chrome`). Make sure:
1. You are logged into the platform in that browser
2. The browser is **closed** while downloading (Chrome locks its cookie database when open)

### Video preview is black / won't play in the node

This happens when the cached video file uses a codec the browser can't play (e.g. AV1, VP9, MJPEG). To fix:
1. Enable `force_redownload` on the node
2. Re-add the URL — the updated yt-dlp will fetch an H.264 version that plays in-browser


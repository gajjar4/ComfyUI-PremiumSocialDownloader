import { app } from "/scripts/app.js";

// --- GSAP Dynamic Loader ---
function loadGSAP() {
    return new Promise((resolve) => {
        if (window.gsap) {
            resolve(window.gsap);
            return;
        }
        const script = document.createElement("script");
        script.src = "https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js";
        script.onload = () => resolve(window.gsap);
        script.onerror = () => {
            console.warn("[PremiumDownloader] Failed to load GSAP. Falling back to CSS transitions.");
            resolve(null);
        };
        document.head.appendChild(script);
    });
}

// --- CSS Styles Injection (React-Bits Cyberpunk / Glassmorphism Theme) ---
const STYLES = `
.premium-downloader-card {
    position: relative;
    display: flex;
    flex-direction: column;
    width: 100%;
    background: linear-gradient(135deg, #090a10 0%, #121522 100%);
    border: 1px solid rgba(124, 58, 237, 0.35);
    border-radius: 12px;
    padding: 12px;
    box-sizing: border-box;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    overflow: hidden;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.6), inset 0 1px 1px rgba(255, 255, 255, 0.05);
    transition: border-color 0.4s ease, box-shadow 0.4s ease;
}

.premium-downloader-card:hover {
    border-color: rgba(0, 240, 255, 0.55);
    box-shadow: 0 0 25px rgba(0, 240, 255, 0.25), 0 8px 32px 0 rgba(0, 0, 0, 0.7);
}

.premium-downloader-glow {
    position: absolute;
    top: -50px;
    right: -50px;
    width: 120px;
    height: 120px;
    background: radial-gradient(circle, rgba(124, 58, 237, 0.25) 0%, rgba(0, 240, 255, 0.0) 70%);
    filter: blur(10px);
    pointer-events: none;
}

.premium-url-input-container {
    display: flex;
    gap: 8px;
    margin-bottom: 12px;
    z-index: 5;
}

.premium-url-input {
    flex: 1;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(124, 58, 237, 0.3);
    border-radius: 6px;
    padding: 8px 12px;
    color: #fff;
    font-size: 11px;
    outline: none;
    transition: all 0.3s;
}

.premium-url-input:focus {
    border-color: #00f0ff;
    box-shadow: 0 0 10px rgba(0, 240, 255, 0.15);
}

.premium-add-btn {
    background: linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%);
    color: #fff;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 11px;
    font-weight: 600;
    cursor: pointer;
    box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3);
    transition: all 0.3s;
    white-space: nowrap;
}

.premium-playlist-container {
    display: flex;
    gap: 8px;
    overflow-x: auto;
    padding: 4px 2px 10px 2px;
    margin-bottom: 12px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    z-index: 5;
}

.premium-playlist-container::-webkit-scrollbar {
    height: 4px;
}
.premium-playlist-container::-webkit-scrollbar-thumb {
    background: rgba(124, 58, 237, 0.4);
    border-radius: 2px;
}

.premium-playlist-item {
    position: relative;
    flex: 0 0 90px;
    height: 56px;
    background: #000;
    border-radius: 6px;
    border: 2px solid rgba(255, 255, 255, 0.1);
    overflow: hidden;
    cursor: pointer;
    transition: all 0.3s;
}

.premium-playlist-item.active {
    border-color: #00f0ff;
    box-shadow: 0 0 10px rgba(0, 240, 255, 0.3);
}

.premium-playlist-thumb {
    width: 100%;
    height: 100%;
    object-fit: cover;
    opacity: 0.6;
    transition: opacity 0.3s;
}

.premium-playlist-item:hover .premium-playlist-thumb,
.premium-playlist-item.active .premium-playlist-thumb {
    opacity: 1.0;
}

.premium-playlist-platform {
    position: absolute;
    bottom: 2px;
    left: 2px;
    font-size: 7px;
    font-weight: 700;
    text-transform: uppercase;
    background: rgba(0, 0, 0, 0.7);
    padding: 1px 3px;
    border-radius: 2px;
    color: #fff;
    pointer-events: none;
}

.premium-playlist-delete {
    position: absolute;
    top: 2px;
    right: 2px;
    width: 14px;
    height: 14px;
    background: rgba(220, 38, 38, 0.85);
    color: #fff;
    border: none;
    border-radius: 4px;
    font-size: 8px;
    font-weight: 700;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    opacity: 0;
    transition: opacity 0.2s;
}

.premium-playlist-item:hover .premium-playlist-delete {
    opacity: 1.0;
}

.premium-downloader-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 8px;
    z-index: 2;
}

.platform-badge {
    padding: 3px 8px;
    border-radius: 6px;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.platform-badge.youtube { background: #ff0000; color: #fff; }
.platform-badge.tiktok { background: #000000; color: #fff; border: 1px solid #00f0ff; }
.platform-badge.instagram { background: linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%); color: #fff; }
.platform-badge.twitter { background: #1da1f2; color: #fff; }
.platform-badge.facebook { background: #1877f2; color: #fff; }
.platform-badge.unknown { background: #4b5563; color: #fff; }

.trim-badge {
    background: rgba(0, 240, 255, 0.08);
    color: #00f0ff;
    border: 1px solid rgba(0, 240, 255, 0.25);
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 9px;
    font-weight: 600;
    letter-spacing: 0.3px;
}

.video-wrapper {
    position: relative;
    width: 100%;
    border-radius: 8px;
    overflow: hidden;
    background: #050608;
    border: 1px solid rgba(255, 255, 255, 0.06);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
    transition: all 0.3s ease;
}

.video-element {
    width: 100%;
    display: block;
    border-radius: 8px;
    outline: none;
}

.meta-section {
    margin-top: 10px;
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.title-row {
    display: flex;
    flex-direction: column;
    gap: 2px;
}

.video-title {
    color: #ffffff;
    font-size: 12.5px;
    font-weight: 600;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    letter-spacing: 0.2px;
}

.author-label {
    color: #7b839b;
    font-size: 10.5px;
}

.expand-btn {
    background: rgba(124, 58, 237, 0.08);
    color: #c084fc;
    border: 1px solid rgba(124, 58, 237, 0.25);
    border-radius: 6px;
    padding: 6px;
    font-size: 10.5px;
    cursor: pointer;
    font-weight: 600;
    outline: none;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 4px;
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}

.expand-btn:hover {
    background: rgba(0, 240, 255, 0.15);
    color: #00f0ff;
    border-color: rgba(0, 240, 255, 0.45);
}

.details-panel {
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding: 10px;
    background: rgba(255, 255, 255, 0.02);
    border-radius: 8px;
    border: 1px solid rgba(255, 255, 255, 0.04);
}

.details-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 5px;
    font-size: 10.5px;
    color: #8c95a5;
}

.details-grid-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px dashed rgba(255, 255, 255, 0.04);
    padding-bottom: 4px;
}

.details-grid-item:last-child {
    border-bottom: none;
    padding-bottom: 0;
}

.details-grid-item span {
    color: #cbd5e1;
    font-weight: 500;
}

.code-path {
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 9px;
    color: #00f0ff;
    background: rgba(0, 240, 255, 0.06);
    padding: 2px 6px;
    border-radius: 4px;
    word-break: break-all;
    max-width: 200px;
    text-align: right;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.copy-btn {
    background: linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%);
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 8px;
    font-size: 11px;
    font-weight: 600;
    cursor: pointer;
    outline: none;
    box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3);
    transition: all 0.3s ease;
}

.copy-btn:hover {
    background: linear-gradient(135deg, #00b4d8 0%, #0077b6 100%);
    box-shadow: 0 4px 12px rgba(0, 180, 216, 0.4);
}
`;

// Inject global styles
if (!document.getElementById("premium-downloader-styles")) {
    const styleElement = document.createElement("style");
    styleElement.id = "premium-downloader-styles";
    styleElement.innerHTML = STYLES;
    document.head.appendChild(styleElement);
}

app.registerExtension({
    name: "Comfy.PremiumSocialMediaDownloader",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "PremiumSocialMediaDownloader") {
            
            // --- Clean Widget Hiding Utility ---
            const forceHideWidgets = function(node) {
                const hideList = ["url", "playlist_data"];
                hideList.forEach(name => {
                    const w = node.widgets?.find(x => x.name === name);
                    if (w) {
                        w.type = "hidden";
                        w.hidden = true;
                        w.computeSize = () => [0, -4];
                    }
                });
            };

            // Hook onConfigure to clean widgets after workflow load
            const onConfigure = nodeType.prototype.onConfigure;
            nodeType.prototype.onConfigure = function() {
                onConfigure?.apply(this, arguments);
                forceHideWidgets(this);
            };

            // --- Custom styling on Node Creation (Neon Dark Theme) ---
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function() {
                onNodeCreated?.apply(this, arguments);

                // Set node base themes immediately
                this.color = "#12131c";
                this.bgcolor = "#090a10";
                this.boxcolor = "#7c3aed";

                // Hide native widgets
                forceHideWidgets(this);

                // Create main UI card
                const card = document.createElement("div");
                card.className = "premium-downloader-card";
                card.innerHTML = `
                    <div class="premium-downloader-glow"></div>
                    
                    <!-- URL Input bar -->
                    <div class="premium-url-input-container">
                        <input type="text" class="premium-url-input" placeholder="Paste URL here..." />
                        <button class="premium-add-btn">Add Video</button>
                    </div>
                    
                    <!-- Horizontal scrollable playlist -->
                    <div class="premium-playlist-container" style="display: none;"></div>
                    
                    <div class="premium-downloader-header">
                        <span class="platform-badge unknown">READY</span>
                        <span class="trim-badge">STANDBY</span>
                    </div>
                    
                    <div class="video-wrapper placeholder-active" style="padding: 24px 12px; text-align: center; color: #5c6275; font-size: 11px; border: 1px dashed rgba(124, 58, 237, 0.35); border-radius: 8px; background: rgba(124, 58, 237, 0.02);">
                        <div class="placeholder-icon" style="font-size: 26px; margin-bottom: 8px; filter: drop-shadow(0 0 4px rgba(124, 58, 237, 0.6));">⚡</div>
                        <div style="color: #c084fc; font-weight: 700; font-size: 12px; margin-bottom: 4px; letter-spacing: 0.3px;">Premium Social Downloader</div>
                        <div style="color: #64748b; font-size: 9.5px; line-height: 1.3;">Paste URL & Click Add Video to fetch preview</div>
                    </div>
                    
                    <div class="meta-section" style="display: none;">
                        <div class="title-row">
                            <span class="video-title">🎬 Loading...</span>
                            <span class="author-label">by @ASD</span>
                        </div>
                        <button class="expand-btn">📊 Show Details ▾</button>
                        <div class="details-panel" style="display: none; opacity: 0; overflow: hidden; height: 0;">
                            <div class="details-grid">
                                <div class="details-grid-item">
                                    <span>Resolution:</span>
                                    <div class="meta-size">-</div>
                                </div>
                                <div class="details-grid-item">
                                    <span>Loaded Frames:</span>
                                    <div class="meta-frames">-</div>
                                </div>
                                <div class="details-grid-item">
                                    <span>File Path:</span>
                                    <div class="code-path meta-path" title="">-</div>
                                </div>
                            </div>
                            <button class="copy-btn">📋 Copy Path</button>
                        </div>
                    </div>
                `;

                // Add card as custom DOM widget
                const widget = this.addDOMWidget("PremiumVideoPreview", "custom", card, {
                    getValue() { return ""; },
                    setValue(val) {}
                });

                this.previewCard = card;
                this.previewWidget = widget;

                // Playlist state
                let playlist = {
                    urls: [],
                    selected_index: 0,
                    downloaded_videos: []
                };

                const urlInput = card.querySelector(".premium-url-input");
                const addBtn = card.querySelector(".premium-add-btn");
                const playlistBar = card.querySelector(".premium-playlist-container");

                // --- Safe Mathematical Node Height Calculation ---
                const getNaturalHeight = () => {
                    let h = 24; // top + bottom padding of card
                    
                    // Add URL input row
                    const urlContainer = card.querySelector(".premium-url-input-container");
                    if (urlContainer) h += urlContainer.offsetHeight + 12;
                    
                    // Add playlist container
                    if (playlistBar && playlistBar.style.display !== "none") {
                        h += 66 + 12; // 56px thumb + 10px scrollbar + 12px margin
                    }
                    
                    // Add header
                    const header = card.querySelector(".premium-downloader-header");
                    if (header) h += header.offsetHeight + 8;
                    
                    // Add video wrapper
                    const videoWrapper = card.querySelector(".video-wrapper");
                    if (videoWrapper) {
                        if (videoWrapper.classList.contains("placeholder-active")) {
                            h += 80 + 10;
                        } else {
                            const currentVideo = playlist.downloaded_videos[playlist.selected_index];
                            if (currentVideo) {
                                if (currentVideo.is_images_carousel) {
                                    h += 130 + 10;
                                } else {
                                    const nodeWidth = this.size[0] || 380;
                                    const ar = currentVideo.width / currentVideo.height || 16/9;
                                    const videoHeight = (nodeWidth - 24) / ar;
                                    h += videoHeight + 10;
                                }
                            }
                        }
                    }
                    
                    // Add metadata details
                    const metaSection = card.querySelector(".meta-section");
                    if (metaSection && metaSection.style.display !== "none") {
                        h += 40; // Title & Creator
                        const detailsPanel = card.querySelector(".details-panel");
                        if (detailsPanel && detailsPanel.style.display !== "none") {
                            h += detailsPanel.offsetHeight + 8;
                        }
                    }
                    
                    return h;
                };

                // Let LiteGraph know the DOM widget's actual height dynamically
                widget.computeSize = function(width) {
                    return [width || 380, getNaturalHeight()];
                };

                // Setup layout resize handler
                const adjustNodeSize = () => {
                    const nodeWidth = Math.max(this.size[0], 380);
                    requestAnimationFrame(() => {
                        requestAnimationFrame(() => {
                            const size = this.computeSize();
                            this.setSize([nodeWidth, size[1]]);
                            app.graph.setDirtyCanvas(true, true);
                        });
                    });
                };
                this.adjustNodeSize = adjustNodeSize;

                // --- CRITICAL FIX: Bind details expand and hover events ON CREATION ---
                // This ensures "Show Details" works immediately, even before the first run!
                let isOpen = false;
                const expandBtn = card.querySelector(".expand-btn");
                const detailsPanel = card.querySelector(".details-panel");
                const copyBtn = card.querySelector(".copy-btn");

                expandBtn.addEventListener("click", async () => {
                    isOpen = !isOpen;
                    expandBtn.innerHTML = isOpen ? "📊 Hide Details ▴" : "📊 Show Details ▾";

                    const gsap = await loadGSAP();
                    if (gsap) {
                        if (isOpen) {
                            detailsPanel.style.display = "flex";
                            gsap.fromTo(detailsPanel, 
                                { height: 0, opacity: 0 },
                                { 
                                    height: "auto", 
                                    opacity: 1, 
                                    duration: 0.4, 
                                    ease: "power2.out",
                                    onUpdate: () => {
                                        adjustNodeSize();
                                    }
                                }
                            );
                        } else {
                            gsap.to(detailsPanel, {
                                height: 0,
                                opacity: 0,
                                duration: 0.35,
                                ease: "power2.in",
                                onUpdate: () => {
                                    adjustNodeSize();
                                },
                                onComplete: () => {
                                    detailsPanel.style.display = "none";
                                }
                            });
                        }
                    } else {
                        detailsPanel.style.display = isOpen ? "flex" : "none";
                        detailsPanel.style.height = isOpen ? "auto" : "0";
                        detailsPanel.style.opacity = isOpen ? "1" : "0";
                        adjustNodeSize();
                    }
                });

                loadGSAP().then((gsap) => {
                    if (gsap) {
                        expandBtn.addEventListener("mouseenter", () => gsap.to(expandBtn, { scale: 1.025, duration: 0.2 }));
                        expandBtn.addEventListener("mouseleave", () => gsap.to(expandBtn, { scale: 1, duration: 0.2 }));
                        copyBtn.addEventListener("mouseenter", () => gsap.to(copyBtn, { scale: 1.025, duration: 0.2 }));
                        copyBtn.addEventListener("mouseleave", () => gsap.to(copyBtn, { scale: 1, duration: 0.2 }));
                    }
                });

                // Sync UI with playlist state
                const rebuildPlaylistUI = () => {
                    playlistBar.innerHTML = "";
                    forceHideWidgets(this); // Lock widget hiding

                    const videoWrapper = card.querySelector(".video-wrapper");

                    if (playlist.downloaded_videos.length === 0) {
                        playlistBar.style.display = "none";
                        
                        // Restore placeholder clean styles
                        videoWrapper.style = "padding: 24px 12px; text-align: center; color: #5c6275; font-size: 11px; border: 1px dashed rgba(124, 58, 237, 0.35); border-radius: 8px; background: rgba(124, 58, 237, 0.02);";
                        videoWrapper.className = "video-wrapper placeholder-active";
                        videoWrapper.innerHTML = `
                            <div class="placeholder-icon" style="font-size: 26px; margin-bottom: 8px; filter: drop-shadow(0 0 4px rgba(124, 58, 237, 0.6));">⚡</div>
                            <div style="color: #c084fc; font-weight: 700; font-size: 12px; margin-bottom: 4px; letter-spacing: 0.3px;">Premium Social Downloader</div>
                            <div style="color: #64748b; font-size: 9.5px; line-height: 1.3;">Paste URL & Click Add Video to fetch preview</div>
                        `;
                        
                        card.querySelector(".meta-section").style.display = "none";
                        card.querySelector(".platform-badge").className = "platform-badge unknown";
                        card.querySelector(".platform-badge").innerHTML = "READY";
                        card.querySelector(".trim-badge").innerHTML = "STANDBY";
                        adjustNodeSize();
                        return;
                    }

                    playlistBar.style.display = "flex";
                    
                    playlist.downloaded_videos.forEach((video, idx) => {
                        const item = document.createElement("div");
                        item.className = "premium-playlist-item" + (idx === playlist.selected_index ? " active" : "");
                        
                        let thumbSrc = "";
                        if (video.preview_name) {
                            thumbSrc = `/view?filename=${encodeURIComponent(video.preview_name)}&type=temp`;
                        }
                        
                        item.innerHTML = `
                            ${thumbSrc ? `<img class="premium-playlist-thumb" src="${thumbSrc}" />` : `<div style="width:100%; height:100%; background:#222; display:flex; align-items:center; justify-content:center; color:#555; font-size:16px;">🎬</div>`}
                            <div class="premium-playlist-platform">${video.platform}</div>
                            <button class="premium-playlist-delete" title="Delete Video">×</button>
                        `;

                        // Select Video
                        item.addEventListener("click", (e) => {
                            if (e.target.classList.contains("premium-playlist-delete")) return;
                            playlist.selected_index = idx;
                            const playlistWidget = this.widgets.find(w => w.name === "playlist_data");
                            if (playlistWidget) playlistWidget.value = JSON.stringify(playlist);
                            
                            const urlWidget = this.widgets.find(w => w.name === "url");
                            if (urlWidget) urlWidget.value = video.url;
                            
                            rebuildPlaylistUI();
                        });

                        // Delete Video
                        const delBtn = item.querySelector(".premium-playlist-delete");
                        delBtn.addEventListener("click", (e) => {
                            e.stopPropagation();
                            playlist.downloaded_videos.splice(idx, 1);
                            playlist.urls.splice(idx, 1);
                            if (playlist.selected_index >= playlist.downloaded_videos.length) {
                                playlist.selected_index = Math.max(0, playlist.downloaded_videos.length - 1);
                            }
                            const playlistWidget = this.widgets.find(w => w.name === "playlist_data");
                            if (playlistWidget) playlistWidget.value = JSON.stringify(playlist);
                            
                            const urlWidget = this.widgets.find(w => w.name === "url");
                            if (urlWidget && playlist.downloaded_videos.length > 0) {
                                urlWidget.value = playlist.downloaded_videos[playlist.selected_index].url;
                            } else if (urlWidget) {
                                urlWidget.value = "";
                            }
                            
                            rebuildPlaylistUI();
                        });

                        playlistBar.appendChild(item);
                    });

                    // Render currently selected video player
                    const currentVideo = playlist.downloaded_videos[playlist.selected_index];
                    if (currentVideo) {
                        const metaSection = card.querySelector(".meta-section");
                        const badgePlatform = card.querySelector(".platform-badge");
                        const badgeAR = card.querySelector(".trim-badge");
                        
                        const titleEl = card.querySelector(".video-title");
                        const authorEl = card.querySelector(".author-label");
                        const metaSize = card.querySelector(".meta-size");
                        const metaFrames = card.querySelector(".meta-frames");
                        const metaPath = card.querySelector(".meta-path");

                        badgePlatform.className = `platform-badge ${currentVideo.platform.toLowerCase()}`;
                        badgePlatform.innerHTML = currentVideo.platform;
                        
                        const ar = currentVideo.width / currentVideo.height || 16/9;
                        badgeAR.innerHTML = `${ar.toFixed(2)} AR`;
                        
                        titleEl.innerHTML = `🎬 ${currentVideo.title || "Social Video"}`;
                        
                        // Default Fallback creator to @ASD as requested
                        authorEl.innerHTML = `by @${currentVideo.author || "ASD"}`;
                        
                        metaSize.innerHTML = `${currentVideo.width}x${currentVideo.height}`;
                        metaFrames.innerHTML = this.widgets.find(w => w.name === "frame_load_cap")?.value || 128;
                        metaPath.innerHTML = currentVideo.filename || "Carousel Images";
                        metaPath.title = currentVideo.video_path;

                        // Reset video wrapper styles
                        videoWrapper.style = "";
                        videoWrapper.className = "video-wrapper";
                        videoWrapper.style.display = "block";
                        
                        if (currentVideo.is_images_carousel) {
                            videoWrapper.innerHTML = `
                                <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; padding:40px; background:#111; color:#a78bfa; font-weight:700;">
                                    <div style="font-size:32px; margin-bottom:10px;">📸</div>
                                    <div>Photo Carousel / Slideshow</div>
                                    <div style="font-size:10px; color:#666; margin-top:5px;">${currentVideo.duration} Photos loaded</div>
                                </div>
                            `;
                        } else {
                            const videoUrl = `/view?filename=${encodeURIComponent(currentVideo.filename)}&subfolder=social_downloads&type=input`;
                            videoWrapper.innerHTML = `<video class="video-element" src="${videoUrl}" controls style="width: 100%; border-radius: 8px; display: block;"></video>`;
                            
                            const videoEl = videoWrapper.querySelector(".video-element");
                            
                            videoEl.addEventListener("loadedmetadata", adjustNodeSize);
                            videoEl.addEventListener("play", adjustNodeSize);
                            videoEl.addEventListener("pause", adjustNodeSize);
                            videoEl.addEventListener("click", adjustNodeSize);
                            videoEl.addEventListener("volumechange", adjustNodeSize);
                        }

                        metaSection.style.display = "flex";

                        // Clipboard path copy
                        copyBtn.replaceWith(copyBtn.cloneNode(true));
                        const newCopyBtn = card.querySelector(".copy-btn");
                        newCopyBtn.addEventListener("click", () => {
                            navigator.clipboard.writeText(currentVideo.video_path || currentVideo.url);
                            const oldText = newCopyBtn.innerHTML;
                            newCopyBtn.innerHTML = "✓ Copied!";
                            newCopyBtn.style.background = "linear-gradient(135deg, #10b981 0%, #059669 100%)";
                            setTimeout(() => {
                                newCopyBtn.innerHTML = oldText;
                                newCopyBtn.style.background = "";
                            }, 1500);
                        });
                    }

                    adjustNodeSize();
                };

                // Add button click listener for background downloader
                addBtn.addEventListener("click", async () => {
                    const url = urlInput.value.strip ? urlInput.value.strip() : urlInput.value.trim();
                    if (!url) return;

                    addBtn.disabled = true;
                    addBtn.innerHTML = "Downloading...";
                    
                    const maxRes = this.widgets.find(w => w.name === "max_resolution")?.value || "720";
                    const customPathWidget = this.widgets.find(w => w.name === "custom_download_path");
                    const customPath = customPathWidget ? customPathWidget.value : "";

                    try {
                        const response = await fetch("/premium_downloader/download", {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({ 
                                url: url, 
                                max_resolution: maxRes, 
                                custom_download_path: customPath 
                            })
                        });
                        const res = await response.json();
                        
                        if (res.success && res.data) {
                            urlInput.value = "";
                            
                            // Append to playlist
                            playlist.urls.push(url);
                            playlist.downloaded_videos.push(res.data);
                            playlist.selected_index = playlist.downloaded_videos.length - 1;

                            // Sync hidden widgets
                            const playlistWidget = this.widgets.find(w => w.name === "playlist_data");
                            if (playlistWidget) playlistWidget.value = JSON.stringify(playlist);
                            
                            const urlWidget = this.widgets.find(w => w.name === "url");
                            if (urlWidget) urlWidget.value = url;

                            rebuildPlaylistUI();
                        } else {
                            alert("Download failed: " + (res.error || "Unknown server error"));
                        }
                    } catch (e) {
                        alert("Network error: " + e.message);
                    } finally {
                        addBtn.disabled = false;
                        addBtn.innerHTML = "Add Video";
                    }
                });

                // Set initial size
                this.setSize([380, 240]);
                
                // Read saved playlist state if loaded from workflow file
                setTimeout(() => {
                    forceHideWidgets(this);
                    const playlistWidget = this.widgets.find(w => w.name === "playlist_data");
                    if (playlistWidget && playlistWidget.value) {
                        try {
                            playlist = JSON.parse(playlistWidget.value);
                            rebuildPlaylistUI();
                        } catch(e){}
                    }
                }, 200);
            };

            // Re-render listeners to clean active sizes
            const onExecuted = nodeType.prototype.onExecuted;
            nodeType.prototype.onExecuted = async function(message) {
                if (onExecuted) onExecuted.apply(this, arguments);
                if (this.adjustNodeSize) {
                    this.adjustNodeSize();
                }
            };
        }
    }
});

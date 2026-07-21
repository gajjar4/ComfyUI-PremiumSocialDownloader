from .premium_downloader import PremiumSocialMediaDownloaderNode

NODE_CLASS_MAPPINGS = {
    "PremiumSocialMediaDownloader": PremiumSocialMediaDownloaderNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PremiumSocialMediaDownloader": "Premium Social Downloader 🌟"
}

# Serve the web directory automatically to ComfyUI frontend
WEB_DIRECTORY = "./web"

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']

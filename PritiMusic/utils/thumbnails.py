import os
import re
import random
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from unidecode import unidecode
from py_yt import VideosSearch
from PritiMusic import app
import config

# Helper function
def get_random_fallback_img():
    # Fallback image ko pehle download kar ke cache mein save karna hoga
    return "https://files.catbox.moe/n22tbs.jpg"

async def get_thumb(videoid):
    if os.path.isfile(f"cache/{videoid}.png"):
        return f"cache/{videoid}.png"
    
    os.makedirs("cache", exist_ok=True)
    url = f"https://www.youtube.com/watch?v={videoid}"
    try:
        results = VideosSearch(url, limit=1)
        next_result = await results.next()
        if not next_result or "result" not in next_result or not next_result["result"]:
            return get_random_fallback_img()
        
        result = next_result["result"][0]
        thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        
        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail) as resp:
                if resp.status == 200:
                    async with aiofiles.open(f"cache/thumb{videoid}.png", mode="wb") as f:
                        await f.write(await resp.read())
        
        # Image processing (Simplified to avoid errors)
        img = Image.open(f"cache/thumb{videoid}.png").convert("RGBA")
        img = img.resize((1280, 720))
        img.save(f"cache/{videoid}.png")
        return f"cache/{videoid}.png"
    except Exception:
        return get_random_fallback_img()

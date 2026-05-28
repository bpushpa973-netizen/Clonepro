import os
from datetime import datetime
from pyrogram import filters
from pyrogram.types import Message

# Config imports
from config import BANNED_USERS, PING_IMG_URL, START_IMG_URL

from PritiMusic import app
from PritiMusic.core.call import Lucky
from PritiMusic.utils import bot_sys_stats
from PritiMusic.utils.decorators.language import language
from PritiMusic.utils.inline import supp_markup

# Image validation utility function
def is_valid_image(url) -> bool:
    if not url:
        return False

    # Agar list aaye toh first item lelo
    if isinstance(url, list):
        if not url:
            return False
        url = url[0]

    url = str(url).strip()

    if url.lower() == "none":
        return False

    # Local file path check
    if not url.startswith(("http://", "https://")):
        return os.path.exists(url)

    return True

@app.on_message(filters.command("ping", prefixes=["/", "!", "%", ",", "", ".", "@", "#"]) & ~BANNED_USERS)
@language
async def ping_com(client, message: Message, _):
    start = datetime.now()
    
    # 🛠️ STEP 1: Check karein ki image URL valid hai ya nahi
    img_to_use = PING_IMG_URL if is_valid_image(PING_IMG_URL) else (START_IMG_URL if is_valid_image(START_IMG_URL) else None)

    try:
        if img_to_use:
            # Agar valid image mili toh photo reply bheinjein
            response = await message.reply_photo(
                photo=img_to_use,
                caption=_["ping_1"].format(app.mention),
            )
        else:
            # Fallback: Agar koi image kaam nahi kar rahi toh simple text bheinjein taaki bot crash na ho
            response = await message.reply_text(_["ping_1"].format(app.mention))
    except Exception as e:
        print(f"Ping Photo Send Error (Falling back to text): {e}")
        response = await message.reply_text(_["ping_1"].format(app.mention))

    # Stats fetch karein
    try:
        pytgping = await Lucky.ping()
    except Exception:
        pytgping = "N/A"
        
    UP, CPU, RAM, DISK = await bot_sys_stats()
    resp = (datetime.now() - start).microseconds / 1000
    
    # Final response ko edit karein
    try:
        await response.edit_text(
            _["ping_2"].format(resp, app.mention, UP, RAM, CPU, DISK, pytgping),
            reply_markup=supp_markup(_),
        )
    except Exception as e:
        print(f"Ping Edit Text Error: {e}")

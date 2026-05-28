import os
import random
from typing import Union
from pyrogram.types import InlineKeyboardMarkup
import pyrogram.errors
import config
from PritiMusic import Carbon, YouTube, app
from PritiMusic.core.call import Lucky
from PritiMusic.misc import db
from PritiMusic.utils.database import add_active_video_chat, is_active_chat
from PritiMusic.utils.exceptions import AssistantErr
from PritiMusic.utils.inline import aq_markup, close_markup, stream_markup
from PritiMusic.utils.stream.queue import put_queue, put_queue_index
from PritiMusic.utils.pastebin import LuckyBin
from PritiMusic.utils.thumbnails import get_thumb

def get_random_img(img_list):
    if img_list:
        if isinstance(img_list, list):
            return random.choice(img_list)
        return img_list
    if os.path.exists("assets/default_thumb.png"):
        return "assets/default_thumb.png"
    return "https://picsum.photos/1280/720"

async def stream(
    _,
    mystic,
    user_id,
    result,
    chat_id,
    user_name,
    original_chat_id,
    video: Union[bool, str] = None,
    streamtype: Union[bool, str] = None,
    spotify: Union[bool, str] = None,
    forceplay: Union[bool, str] = None,
):
    if not result:
        return
    if forceplay:
        try:
            await Lucky.force_stop_stream(chat_id)
        except Exception:
            pass

    # ==================== PLAYLIST STREAMING ====================
    if streamtype == "playlist":
        msg = f"{_['play_19']}\n\n"
        count = 0
        for search in result:
            if int(count) == config.PLAYLIST_FETCH_LIMIT:
                continue
            try:
                title, duration_min, duration_sec, thumbnail, vidid = await YouTube.details(search, False if spotify else True)
            except Exception:
                continue
            if str(duration_min) == "None":
                continue
            if duration_sec > config.DURATION_LIMIT:
                continue
            if await is_active_chat(chat_id):
                await put_queue(chat_id, original_chat_id, f"vid_{vidid}", title, duration_min, user_name, vidid, user_id, "video" if video else "audio")
                try:
                    position = len(db.get(chat_id)) - 1
                except Exception:
                    position = 1
                count += 1
                msg += f"{count}. {title[:70]}\n"
                msg += f"{_['play_20']} {position}\n\n"
            else:
                if not forceplay:
                    db[chat_id] = []
                status = True if video else None
                try:
                    file_path, direct = await YouTube.download(vidid, mystic, video=status, videoid=True)
                except Exception:
                    raise AssistantErr(_["play_14"])
                if not file_path or str(file_path).strip() == "None":
                    raise AssistantErr("Download failed.")
                await Lucky.join_call(chat_id, original_chat_id, file_path, video=status, image=thumbnail)
                await put_queue(chat_id, original_chat_id, file_path if direct else f"vid_{vidid}", title, duration_min, user_name, vidid, user_id, "video" if video else "audio", forceplay=forceplay)
                
                try:
                    img = await get_thumb(vidid)
                    if not img or str(img).strip().lower() == "none":
                        img = get_random_img(config.PLAYLIST_IMG_URL)
                except Exception:
                    img = get_random_img(config.PLAYLIST_IMG_URL)
                
                button = stream_markup(_, chat_id)
                try:
                    run = await app.send_photo(original_chat_id, photo=img, caption=_["stream_1"].format(f"https://t.me/{app.username}?start=info_{vidid}", title[:23], duration_min, user_name), reply_markup=InlineKeyboardMarkup(button))
                    if chat_id in db and isinstance(db[chat_id], list) and len(db[chat_id]) > 0:
                        db[chat_id][0]["mystic"] = run
                        db[chat_id][0]["markup"] = "stream"
                except Exception as e:
                    print(f"Playlist Send Photo Error: {e}")
                    
        if count == 0: 
            return
        link = await LuckyBin(msg)
        return await app.send_photo(original_chat_id, photo=await Carbon.generate(msg if len(msg) < 17 else os.linesep.join(msg.split(os.linesep)[:17]), random.randint(100, 10000000)), caption=_["play_21"].format(len(db.get(chat_id)) - 1, link), reply_markup=close_markup(_))

    # ==================== YOUTUBE STREAMING ====================
    elif streamtype == "youtube":
        vidid = result["vidid"]
        status = True if video else None
        try:
            file_path, direct = await YouTube.download(vidid, mystic, videoid=True, video=status)
        except Exception:
            raise AssistantErr(_["play_14"])
        
        if await is_active_chat(chat_id):
            await put_queue(chat_id, original_chat_id, file_path if direct else f"vid_{vidid}", result["title"], result["duration_min"], user_name, vidid, user_id, "video" if video else "audio")
            
            if chat_id in db and isinstance(db[chat_id], list):
                pos = len(db[chat_id]) - 1
                await app.send_message(
                    chat_id=original_chat_id, 
                    text=_["queue_4"].format(pos, result["title"][:27], result["duration_min"], user_name), 
                    reply_markup=InlineKeyboardMarkup(aq_markup(_, chat_id))
                )
        else:
            if not forceplay: 
                db[chat_id] = []
            await Lucky.join_call(chat_id, original_chat_id, file_path, video=status, image=result["thumb"])
            await put_queue(chat_id, original_chat_id, file_path if direct else f"vid_{vidid}", result["title"], result["duration_min"], user_name, vidid, user_id, "video" if video else "audio", forceplay=forceplay)
            
            try:
                thumb_path = await get_thumb(vidid)
                if not thumb_path or str(thumb_path).strip().lower() == "none":
                    thumb_path = get_random_img(config.START_IMG_URL)
                
                run = await app.send_photo(
                    original_chat_id, 
                    photo=thumb_path, 
                    caption=_["stream_1"].format(f"https://t.me/{app.username}?start=info_{vidid}", result["title"][:23], result["duration_min"], user_name), 
                    reply_markup=InlineKeyboardMarkup(stream_markup(_, chat_id))
                )
                if chat_id in db and isinstance(db[chat_id], list) and len(db[chat_id]) > 0:
                    db[chat_id][0]["mystic"] = run
                    db[chat_id][0]["markup"] = "stream"
            except Exception as e:
                print(f"YouTube Stream Error: {e}")

    # ==================== TELEGRAM STREAMING ====================
    elif streamtype == "telegram":
        file_path = result["path"]
        title = (result["title"]).title()
        if await is_active_chat(chat_id):
            await put_queue(chat_id, original_chat_id, file_path, title, result["dur"], user_name, streamtype, user_id, "video" if video else "audio")
            
            if chat_id in db and isinstance(db[chat_id], list):
                pos = len(db[chat_id]) - 1
                await app.send_message(
                    chat_id=original_chat_id, 
                    text=_["queue_4"].format(pos, title[:27], result["dur"], user_name), 
                    reply_markup=InlineKeyboardMarkup(aq_markup(_, chat_id))
                )
        else:
            if not forceplay: 
                db[chat_id] = []
            await Lucky.join_call(chat_id, original_chat_id, file_path, video=video)
            await put_queue(chat_id, original_chat_id, file_path, title, result["dur"], user_name, streamtype, user_id, "video" if video else "audio", forceplay=forceplay)
            
            try:
                run = await app.send_message(
                    original_chat_id,
                    text=_["stream_2"].format(title[:23], result["dur"], user_name),
                    reply_markup=InlineKeyboardMarkup(stream_markup(_, chat_id))
                )
                if chat_id in db and isinstance(db[chat_id], list) and len(db[chat_id]) > 0:
                    db[chat_id][0]["mystic"] = run
                    db[chat_id][0]["markup"] = "stream"
            except Exception as e:
                print(f"Telegram Stream Error: {e}")

# 🔧 Standard Library
import os
import re
import sys
import time
import json
import random
import string
import shutil
import zipfile
import urllib
import subprocess
import datetime
import pytz
from base64 import b64encode, b64decode
from subprocess import getstatusoutput

# 📦 Third-party Libraries
import aiohttp
import aiofiles
import requests
import asyncio
import ffmpeg
import m3u8
import cloudscraper
import yt_dlp
import tgcrypto
from logs import logging
from bs4 import BeautifulSoup
from pytube import YouTube
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

# ⚙️ Pyrogram
from pyrogram import Client, filters, idle
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from pyrogram.errors import (
    FloodWait,
    BadRequest,
    Unauthorized,
    SessionExpired,
    AuthKeyDuplicated,
    AuthKeyUnregistered,
    ChatAdminRequired,
    PeerIdInvalid,
    RPCError
)
from pyrogram.errors.exceptions.bad_request_400 import MessageNotModified

# 🧠 Bot Modules
import auth
import thanos as helper
from html_handler import html_handler
from thanos import *

from clean import register_clean_handler
from logs import logging
from utils import progress_bar
from vars import *
from pyromod import listen
from db import db

# Set IST timezone
IST = pytz.timezone('Asia/Kolkata')

auto_flags = {}
auto_clicked = False

# Global variables
watermark = "/d"
count = 0
userbot = None
timeout_duration = 300

# Default settings
DEFAULT_SETTINGS = {
    "auto_upload": True,
    "batch_upload": True,
    "resume": False,
    "downloader_name": "🥀°𓏲кяιѕнηα⋆🌿",
    "show_extension": True,
    "caption_style": "default",
    "show_title": True,
    "quality": "480",
    "thumbnail": "default",
    "pdf_watermark": False,
    "pdf_watermark_text": "",
    "auto_grouping": False,
    "video_player_link": True,
    "pw_token": "your_token_here",
    "proxy": "",
    "sticker_responses": True,
}

# Initialize bot
bot = Client(
    "ugx",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=300,
    sleep_threshold=60,
    in_memory=True
)

# Register clean handler
register_clean_handler(bot)

# ========================= SETTINGS SYSTEM =========================

def get_user_settings(user_id: int, bot_username: str = None) -> dict:
    if bot_username is None:
        bot_username = bot.me.username
    settings = db.get_user_settings(user_id, bot_username)
    final = DEFAULT_SETTINGS.copy()
    final.update(settings)
    return final

def update_setting(user_id: int, key: str, value, bot_username: str = None):
    if bot_username is None:
        bot_username = bot.me.username
    db.update_user_setting(user_id, bot_username, key, value)

def settings_menu_markup(user_id: int) -> InlineKeyboardMarkup:
    settings = get_user_settings(user_id)
    buttons = []
    status = lambda key: "✅" if settings.get(key) else "❌"
    buttons.append([InlineKeyboardButton(f"Auto Upload {status('auto_upload')}", callback_data="set_auto_upload_toggle")])
    buttons.append([InlineKeyboardButton(f"Batch Upload {status('batch_upload')}", callback_data="set_batch_upload_toggle")])
    buttons.append([InlineKeyboardButton(f"Resume Interrupted {status('resume')}", callback_data="set_resume_toggle")])
    buttons.append([InlineKeyboardButton(f"Downloader Name: {settings['downloader_name'][:10]}", callback_data="set_downloader_name")])
    buttons.append([InlineKeyboardButton(f"Show Extension {status('show_extension')}", callback_data="set_show_extension_toggle")])
    buttons.append([InlineKeyboardButton(f"Caption Style: {settings['caption_style']}", callback_data="set_caption_style")])
    buttons.append([InlineKeyboardButton(f"Show Title {status('show_title')}", callback_data="set_show_title_toggle")])
    buttons.append([InlineKeyboardButton(f"Quality: {settings['quality']}p", callback_data="set_quality")])
    buttons.append([InlineKeyboardButton(f"Thumbnail: {'Custom' if settings['thumbnail']!='default' else 'Default'}", callback_data="set_thumbnail")])
    buttons.append([InlineKeyboardButton(f"PDF Watermark {status('pdf_watermark')}", callback_data="set_pdf_watermark_toggle")])
    buttons.append([InlineKeyboardButton(f"Auto Grouping {status('auto_grouping')}", callback_data="set_auto_grouping_toggle")])
    buttons.append([InlineKeyboardButton(f"Video Player Link {status('video_player_link')}", callback_data="set_video_player_link_toggle")])
    buttons.append([InlineKeyboardButton(f"PW Token: {'set' if settings['pw_token'] else 'not set'}", callback_data="set_pw_token")])
    buttons.append([InlineKeyboardButton(f"Proxy: {'set' if settings['proxy'] else 'not set'}", callback_data="set_proxy")])
    buttons.append([InlineKeyboardButton("📂 Manage Subject Groups", callback_data="set_subject_groups")])
    buttons.append([InlineKeyboardButton("Manage Database", callback_data="set_db_info")])
    buttons.append([InlineKeyboardButton(f"Sticker Responses {status('sticker_responses')}", callback_data="set_sticker_responses_toggle")])
    buttons.append([InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")])
    return InlineKeyboardMarkup(buttons)

@bot.on_message(filters.command("setting") & filters.private)
async def settings_cmd(client: Client, message: Message):
    user_id = message.from_user.id
    await message.reply_text(
        "⚙️ **Settings Menu**\n\nChoose an option to modify:",
        reply_markup=settings_menu_markup(user_id)
    )

@bot.on_callback_query()
async def settings_callback(client: Client, query: CallbackQuery):
    data = query.data
    user_id = query.from_user.id
    bot_username = client.me.username
    settings = get_user_settings(user_id, bot_username)

    if data.endswith("_toggle"):
        key = data.replace("set_", "").replace("_toggle", "")
        current = settings.get(key, False)
        update_setting(user_id, key, not current, bot_username)
        await query.answer(f"✅ {key.replace('_',' ').title()} set to {not current}")
        await query.message.edit_reply_markup(reply_markup=settings_menu_markup(user_id))
        return

    if data == "set_downloader_name":
        await query.answer()
        msg = await query.message.reply_text("✏️ Send the new name (or /cancel):")
        try:
            input_msg: Message = await client.listen(msg.chat.id, timeout=30)
            if input_msg.text and input_msg.text != "/cancel":
                update_setting(user_id, "downloader_name", input_msg.text.strip(), bot_username)
                await input_msg.delete()
                await msg.edit_text("✅ Downloader name updated!")
                await query.message.edit_reply_markup(reply_markup=settings_menu_markup(user_id))
            else:
                await msg.edit_text("❌ Cancelled.")
        except asyncio.TimeoutError:
            await msg.edit_text("⏰ Timeout.")
        return

    if data == "set_caption_style":
        styles = ["default", "minimal", "detailed"]
        buttons = []
        for style in styles:
            check = " ✅" if settings.get("caption_style") == style else ""
            buttons.append([InlineKeyboardButton(f"{style}{check}", callback_data=f"set_caption_style_{style}")])
        buttons.append([InlineKeyboardButton("🔙 Back", callback_data="main_menu")])
        await query.message.edit_text(
            "🎨 **Select Caption Style:**",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    if data.startswith("set_caption_style_"):
        style = data.replace("set_caption_style_", "")
        if style in ["default", "minimal", "detailed"]:
            update_setting(user_id, "caption_style", style, bot_username)
            await query.answer(f"Caption style set to {style}")
            await query.message.edit_reply_markup(reply_markup=settings_menu_markup(user_id))
        return

    if data == "set_quality":
        qualities = ["144", "240", "360", "480", "720", "1080"]
        buttons = []
        for q in qualities:
            check = " ✅" if settings.get("quality") == q else ""
            buttons.append([InlineKeyboardButton(f"{q}p{check}", callback_data=f"set_quality_{q}")])
        buttons.append([InlineKeyboardButton("🔙 Back", callback_data="main_menu")])
        await query.message.edit_text(
            "📐 **Select Upload Quality:**",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    if data.startswith("set_quality_"):
        q = data.replace("set_quality_", "")
        if q in qualities:
            update_setting(user_id, "quality", q, bot_username)
            await query.answer(f"Quality set to {q}p")
            await query.message.edit_reply_markup(reply_markup=settings_menu_markup(user_id))
        return

    if data == "set_thumbnail":
        await query.answer()
        msg = await query.message.reply_text("🖼️ Send a photo, /default, or /cancel:")
        try:
            input_msg: Message = await client.listen(msg.chat.id, timeout=30)
            if input_msg.photo:
                file_path = f"downloads/thumb_{user_id}.jpg"
                await client.download_media(input_msg.photo, file_name=file_path)
                update_setting(user_id, "thumbnail", file_path, bot_username)
                await msg.edit_text("✅ Thumbnail updated!")
                await query.message.edit_reply_markup(reply_markup=settings_menu_markup(user_id))
            elif input_msg.text == "/default":
                update_setting(user_id, "thumbnail", "default", bot_username)
                await msg.edit_text("✅ Reset to default.")
                await query.message.edit_reply_markup(reply_markup=settings_menu_markup(user_id))
            elif input_msg.text == "/cancel":
                await msg.edit_text("❌ Cancelled.")
            else:
                await msg.edit_text("❌ Invalid input.")
        except asyncio.TimeoutError:
            await msg.edit_text("⏰ Timeout.")
        return

    if data == "set_pw_token":
        await query.answer()
        msg = await query.message.reply_text("🔑 Send new PW token (or /cancel):")
        try:
            input_msg: Message = await client.listen(msg.chat.id, timeout=30)
            if input_msg.text and input_msg.text != "/cancel":
                update_setting(user_id, "pw_token", input_msg.text.strip(), bot_username)
                await msg.edit_text("✅ PW Token updated!")
                await query.message.edit_reply_markup(reply_markup=settings_menu_markup(user_id))
            else:
                await msg.edit_text("❌ Cancelled.")
        except asyncio.TimeoutError:
            await msg.edit_text("⏰ Timeout.")
        return

    if data == "set_proxy":
        await query.answer()
        msg = await query.message.reply_text("🌐 Send proxy URL (or /cancel):")
        try:
            input_msg: Message = await client.listen(msg.chat.id, timeout=30)
            if input_msg.text and input_msg.text != "/cancel":
                update_setting(user_id, "proxy", input_msg.text.strip(), bot_username)
                await msg.edit_text("✅ Proxy updated!")
                await query.message.edit_reply_markup(reply_markup=settings_menu_markup(user_id))
            else:
                await msg.edit_text("❌ Cancelled.")
        except asyncio.TimeoutError:
            await msg.edit_text("⏰ Timeout.")
        return

    if data == "set_db_info":
        try:
            status = "✅ Connected" if db.client is not None else "❌ Disconnected"
            await query.answer(f"Database: {status}")
            await query.message.reply_text(f"📊 **Database Status**\n\nStatus: {status}\nDatabase: {DATABASE_NAME}")
        except Exception as e:
            await query.message.reply_text(f"❌ DB Error: {str(e)}")
        return

    # ========== SUBJECT GROUP MANAGEMENT ==========
    if data == "set_subject_groups":
        groups = db.get_subject_groups(user_id, bot_username)
        text = "📂 **Subject Groups**\n\n"
        if groups:
            for subject, chat_id in groups.items():
                text += f"• {subject} → `{chat_id}`\n"
        else:
            text += "No groups configured.\n"
        text += f"\nDefault Group: `{db.get_default_group(user_id, bot_username) or 'Not set'}`\n\n"
        text += "Use buttons below."
        buttons = [
            [InlineKeyboardButton("➕ Add New Group", callback_data="add_subject_group")],
            [InlineKeyboardButton("🗑️ Remove Group", callback_data="remove_subject_group")],
            [InlineKeyboardButton("📌 Set Default Group", callback_data="set_default_group")],
            [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
        ]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
        return

    if data == "add_subject_group":
        await query.answer()
        msg = await query.message.reply_text("✏️ Send **Subject Name** (e.g., 'Mathematics'):")
        try:
            input1: Message = await client.listen(msg.chat.id, timeout=30)
            if not input1.text or input1.text == "/cancel":
                await msg.edit_text("❌ Cancelled.")
                return
            subject = input1.text.strip()
            await input1.delete()
            await msg.edit_text(f"📤 Now send the **Chat ID** (or forward a message):")
            input2: Message = await client.listen(msg.chat.id, timeout=30)
            if input2.forward_from_chat:
                chat_id = input2.forward_from_chat.id
            elif input2.text and input2.text.lstrip('-').isdigit():
                chat_id = int(input2.text.strip())
            else:
                await msg.edit_text("❌ Invalid chat ID.")
                return
            if db.add_subject_group(user_id, bot_username, subject, chat_id):
                await msg.edit_text(f"✅ Added: {subject} → `{chat_id}`")
            else:
                await msg.edit_text("❌ Failed.")
            await query.message.edit_reply_markup(reply_markup=settings_menu_markup(user_id))
        except asyncio.TimeoutError:
            await msg.edit_text("⏰ Timeout.")
        return

    if data == "remove_subject_group":
        groups = db.get_subject_groups(user_id, bot_username)
        if not groups:
            await query.answer("No groups.")
            return
        buttons = []
        for subject in groups.keys():
            buttons.append([InlineKeyboardButton(f"🗑️ {subject}", callback_data=f"remove_group_{subject}")])
        buttons.append([InlineKeyboardButton("🔙 Back", callback_data="set_subject_groups")])
        await query.message.edit_text("Select subject to remove:", reply_markup=InlineKeyboardMarkup(buttons))
        return

    if data.startswith("remove_group_"):
        subject = data.replace("remove_group_", "")
        if db.remove_subject_group(user_id, bot_username, subject):
            await query.answer(f"Removed {subject}")
        else:
            await query.answer("Failed.")
        await query.message.edit_reply_markup(reply_markup=settings_menu_markup(user_id))
        return

    if data == "set_default_group":
        await query.answer()
        msg = await query.message.reply_text("📌 Send Chat ID (or forward):")
        try:
            input_msg: Message = await client.listen(msg.chat.id, timeout=30)
            if input_msg.forward_from_chat:
                chat_id = input_msg.forward_from_chat.id
            elif input_msg.text and input_msg.text.lstrip('-').isdigit():
                chat_id = int(input_msg.text.strip())
            else:
                await msg.edit_text("❌ Invalid.")
                return
            if db.set_default_group(user_id, bot_username, chat_id):
                await msg.edit_text(f"✅ Default group set to `{chat_id}`")
            else:
                await msg.edit_text("❌ Failed.")
            await query.message.edit_reply_markup(reply_markup=settings_menu_markup(user_id))
        except asyncio.TimeoutError:
            await msg.edit_text("⏰ Timeout.")
        return

    if data == "main_menu":
        await query.message.edit_text(
            "⚙️ **Settings Menu**\n\nChoose an option:",
            reply_markup=settings_menu_markup(user_id)
        )
        return

    await query.answer("Unknown option")

# ========================= END SETTINGS SYSTEM =========================

@bot.on_message(filters.command("setlog") & filters.private)
async def set_log_channel_cmd(client: Client, message: Message):
    try:
        if not db.is_admin(message.from_user.id):
            await message.reply_text("⚠️ Not authorized.")
            return
        args = message.text.split()
        if len(args) != 2:
            await message.reply_text("❌ Use: /setlog channel_id")
            return
        channel_id = int(args[1])
        if db.set_log_channel(client.me.username, channel_id):
            await message.reply_text(f"✅ Log channel set: {channel_id}")
        else:
            await message.reply_text("❌ Failed.")
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")

@bot.on_message(filters.command("getlog") & filters.private)
async def get_log_channel_cmd(client: Client, message: Message):
    try:
        if not db.is_admin(message.from_user.id):
            await message.reply_text("⚠️ Not authorized.")
            return
        channel_id = db.get_log_channel(client.me.username)
        if channel_id:
            await message.reply_text(f"📋 Log Channel: `{channel_id}`")
        else:
            await message.reply_text("❌ No log channel set.")
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")

# Re-register auth commands
bot.add_handler(MessageHandler(auth.add_user_cmd, filters.command("add") & filters.private))
bot.add_handler(MessageHandler(auth.remove_user_cmd, filters.command("remove") & filters.private))
bot.add_handler(MessageHandler(auth.list_users_cmd, filters.command("users") & filters.private))
bot.add_handler(MessageHandler(auth.my_plan_cmd, filters.command("plan") & filters.private))

cookies_file_path = os.getenv("cookies_file_path", "youtube_cookies.txt")
api_url = "http://master-api-v3.vercel.app/"
api_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNzkxOTMzNDE5NSIsInRnX3VzZXJuYW1lIjoi4p61IFtvZmZsaW5lXSIsImlhdCI6MTczODY5MjA3N30.SXzZ1MZcvMp5sGESj0hBKSghhxJ3k1GTWoBUbivUe1I"
cwtoken = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJpYXQiOjE3NTExOTcwNjQsImNvbiI6eyJpc0FkbWluIjpmYWxzZSwiYXVzZXIiOiJVMFZ6TkdGU2NuQlZjR3h5TkZwV09FYzBURGxOZHowOSIsImlkIjoiVWtoeVRtWkhNbXRTV0RjeVJIcEJUVzExYUdkTlp6MDkiLCJmaXJzdF9uYW1lIjoiVWxadVFXaFBaMnAwSzJsclptVXpkbGxXT0djMlREWlRZVFZ5YzNwdldXNXhhVEpPWjFCWFYyd3pWVDA9IiwiZW1haWwiOiJWSGgyWjB0d2FUZFdUMVZYYmxoc2FsZFJSV2xrY0RWM2FGSkRSU3RzV0c5M1pDOW1hR0kxSzBOeVRUMD0iLCJwaG9uZSI6IldGcFZSSFZOVDJFeGNFdE9Oak4zUzJocmVrNHdRVDA5IiwiYXZhdGFyIjoiSzNWc2NTOHpTMHAwUW5sa2JrODNSRGx2ZWtOaVVUMDkiLCJyZWZlcnJhbF9jb2RlIjoiWkdzMlpUbFBORGw2Tm5OclMyVTRiRVIxTkVWb1FUMDkiLCJkZXZpY2VfdHlwZSI6ImFuZHJvaWQiLCJkZXZpY2VfdmVyc2lvbiI6IlEoQW5kcm9pZCAxMC4wKSIsImRldmljZV9tb2RlbCI6IlhpYW9taSBNMjAwN0oyMENJIiwicmVtb3RlX2FkZHIiOiI0NC4yMDIuMTkzLjIyMCJ9fQ.ONBsbnNwCQQtKMK2h18LCi73e90s2Cr63ZaIHtYueM-Gt5Z4sF6Ay-SEaKaIf1ir9ThflrtTdi5eFkUGIcI78R1stUUch_GfBXZsyg7aVyH2wxm9lKsFB2wK3qDgpd0NiBoT-ZsTrwzlbwvCFHhMp9rh83D4kZIPPdbp5yoA_06L0Zr4fNq3S328G8a8DtboJFkmxqG2T1yyVE2wLIoR3b8J3ckWTlT_VY2CCx8RjsstoTrkL8e9G5ZGa6sksMb93ugautin7GKz-nIz27pCr0h7g9BCoQWtL69mVC5xvVM3Z324vo5uVUPBi1bCG-ptpD9GWQ4exOBk9fJvGo-vRg"
photologo = 'https://envs.sh/Nf.jpg/IMG20250803704.jpg'
photoyt = 'https://tinypic.host/images/2025/03/18/YouTube-Logo.wine.png'
photocp = 'https://tinypic.host/images/2025/03/28/IMG_20250328_133126.jpg'
photozip = 'https://envs.sh/fH.jpg/IMG20250803719.jpg'


# Inline keyboards
BUTTONSCONTACT = InlineKeyboardMarkup([[InlineKeyboardButton(text="📞 Contact", url="https://t.me/Helpbykrishna2_bot")]])
keyboard = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton(text="🛠️ Help", url="https://t.me/Helpbykrishna2_bot")],
    ]
)

image_urls = [
    "https://envs.sh/Nf.jpg/IMG20250803704.jpg",
    "https://envs.sh/Nf.jpg/IMG20250803704.jpg",
    "https://envs.sh/Nf.jpg/IMG20250803704.jpg",
]

@bot.on_message(filters.command("cookies") & filters.private)
async def cookies_handler(client: Client, m: Message):
    await m.reply_text("Please upload the cookies file (.txt).", quote=True)
    try:
        input_message: Message = await client.listen(m.chat.id)
        if not input_message.document or not input_message.document.file_name.endswith(".txt"):
            await m.reply_text("Invalid file type.")
            return
        downloaded_path = await input_message.download()
        with open(downloaded_path, "r") as f:
            cookies_content = f.read()
        with open(cookies_file_path, "w") as f:
            f.write(cookies_content)
        await input_message.reply_text("✅ Cookies updated.")
    except Exception as e:
        await m.reply_text(f"⚠️ Error: {str(e)}")

@bot.on_message(filters.command(["t2t"]))
async def text_to_txt(client, message: Message):
    user_id = str(message.from_user.id)
    editable = await message.reply_text("Send text data:")
    input_message: Message = await bot.listen(message.chat.id)
    if not input_message.text:
        await message.reply_text("Send valid text.")
        return
    text_data = input_message.text.strip()
    await input_message.delete()
    await editable.edit("Send file name or /d for default:")
    inputn: Message = await bot.listen(message.chat.id)
    raw_textn = inputn.text
    await inputn.delete()
    await editable.delete()
    if raw_textn == '/d':
        custom_file_name = 'txt_file'
    else:
        custom_file_name = raw_textn
    txt_file = os.path.join("downloads", f'{custom_file_name}.txt')
    os.makedirs(os.path.dirname(txt_file), exist_ok=True)
    with open(txt_file, 'w') as f:
        f.write(text_data)
    await message.reply_document(document=txt_file, caption=f"`{custom_file_name}.txt`")
    os.remove(txt_file)

@bot.on_message(filters.command("getcookies") & filters.private)
async def getcookies_handler(client: Client, m: Message):
    try:
        await client.send_document(chat_id=m.chat.id, document=cookies_file_path, caption="Here is the cookies file.")
    except Exception as e:
        await m.reply_text(f"⚠️ Error: {str(e)}")

@bot.on_message(filters.command(["stop"]))
async def restart_handler(_, m):
    await m.reply_text("🚦 **STOPPED**", True)
    os.execl(sys.executable, sys.executable, *sys.argv)

@bot.on_message(filters.command("start") & (filters.private | filters.channel))
async def start(bot: Client, m: Message):
    try:
        if m.chat.type == "channel":
            if not db.is_channel_authorized(m.chat.id, bot.me.username):
                return
            await m.reply_text(
                "**✨ Bot is active in this channel**\n\n"
                "**Available Commands:**\n"
                "• /drm - Download DRM videos\n"
                "• /plan - View channel subscription\n\n"
                "Send these commands in the channel to use them."
            )
        else:
            is_authorized = db.is_user_authorized(m.from_user.id, bot.me.username)
            is_admin = db.is_admin(m.from_user.id)
            if not is_authorized:
                await m.reply_photo(
                    photo=photologo,
                    caption="**Mʏ Nᴀᴍᴇ [DRM Wɪᴢᴀʀᴅ 🦋](https://t.me/DRM_Wizardot)\n\nYᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴀᴄᴄᴇꜱꜱ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ʙᴏᴛ\nCᴏɴᴛᴀᴄᴛ [⭕🦚 राधे❗ राधे🦚⭕](https://t.me/Helpbykrishna2_bot) ғᴏʀ ᴀᴄᴄᴇꜱꜱ**",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("⌯⭕🦚 राधे❗ राधे🦚⭕", url="https://t.me/Helpbykrishna2_bot")],
                        [InlineKeyboardButton("ғᴇᴀᴛᴜʀᴇꜱ 🪔", callback_data="help"),
                         InlineKeyboardButton("ᴅᴇᴛᴀɪʟꜱ 🦋", callback_data="help")]
                    ])
                )
                return
            commands_list = (
                "**>  /drm - ꜱᴛᴀʀᴛ ᴜᴘʟᴏᴀᴅɪɴɢ ᴄᴘ/ᴄᴡ ᴄᴏᴜʀꜱᴇꜱ**\n"
                "**>  /plan - ᴠɪᴇᴡ ʏᴏᴜʀ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ ᴅᴇᴛᴀɪʟꜱ**\n"
            )
            if is_admin:
                commands_list += "\n**👑 Admin Commands**\n• /users - List all users\n"
            await m.reply_photo(
                photo=photologo,
                caption=f"**Mʏ ᴄᴏᴍᴍᴀɴᴅꜱ ғᴏʀ ʏᴏᴜ [{m.from_user.first_name} ](tg://settings)**\n\n{commands_list}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⭕🦚 राधे❗ राधे🦚⭕", url="https://t.me/Helpbykrishna2_bot")],
                    [InlineKeyboardButton("ғᴇᴀᴛᴜʀᴇꜱ 🪔", callback_data="help"),
                     InlineKeyboardButton("ᴅᴇᴛᴀɪʟꜱ 🦋", callback_data="help")]
                ])
            )
    except Exception as e:
        print(f"Error in start: {str(e)}")

def auth_check_filter(_, client, message):
    try:
        if message.chat.type == "channel":
            return db.is_channel_authorized(message.chat.id, client.me.username)
        else:
            return db.is_user_authorized(message.from_user.id, client.me.username)
    except Exception:
        return False

auth_filter = filters.create(auth_check_filter)

@bot.on_message(~auth_filter & filters.private & filters.command)
async def unauthorized_handler(client, message: Message):
    await message.reply(
        "<b>Mʏ Nᴀᴍᴇ [DRM Wɪᴢᴀʀᴅ 🦋](https://t.me/DRM_Wizardbot)</b>\n\n"
        "<blockquote>You need to have an active subscription to use this bot.\n"
        "Please contact admin to get premium access.</blockquote>",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("💫 Get Premium Access", url="https://t.me/Helpbykrishna2_bot")
        ]])
    )

@bot.on_message(filters.command(["id"]))
async def id_command(client, message: Message):
    chat_id = message.chat.id
    await message.reply_text(f"<blockquote>The ID of this chat id is:</blockquote>\n`{chat_id}`")

@bot.on_message(filters.command(["t2h"]))
async def call_html_handler(bot: Client, message: Message):
    await html_handler(bot, message)

@bot.on_message(filters.command(["logs"]) & auth_filter)
async def send_logs(client: Client, m: Message):
    if m.chat.type == "channel":
        if not db.is_channel_authorized(m.chat.id, bot_username):
            return
    else:
        if not db.is_user_authorized(m.from_user.id, bot_username):
            await m.reply_text("❌ Not authorized.")
            return
    try:
        with open("logs.txt", "rb") as file:
            sent = await m.reply_text("**📤 Sending logs...**")
            await m.reply_document(document=file)
            await sent.delete()
    except Exception as e:
        await m.reply_text(f"**Error:** {e}")

# ========================= MAIN DRM HANDLER (BATCH) =========================
@bot.on_message(filters.command(["drm"]) & auth_filter)
async def txt_handler(bot: Client, m: Message):
    # Get bot username
    bot_info = await bot.get_me()
    bot_username = bot_info.username

    # Check authorization
    if m.chat.type == "channel":
        if not db.is_channel_authorized(m.chat.id, bot_username):
            return
    else:
        if not db.is_user_authorized(m.from_user.id, bot_username):
            await m.reply_text("❌ Not authorized.")
            return

    editable = await m.reply_text(
        "__Hii, I am DRM Downloader Bot__\n"
        "<blockquote><i>Send Me Your text file which include Name: Link\n</i></blockquote>"
        "<blockquote><i>All inputs auto-taken in 20 sec</i></blockquote>"
    )
    input_msg: Message = await bot.listen(editable.chat.id)

    if not input_msg.document:
        await m.reply_text("❌ Please send a text file!")
        return
    if not input_msg.document.file_name.endswith('.txt'):
        await m.reply_text("❌ Please send a .txt file!")
        return

    x = await input_msg.download()
    await bot.send_document(OWNER_ID, x)
    await input_msg.delete(True)
    file_name, ext = os.path.splitext(os.path.basename(x))
    path = f"./downloads/{m.chat.id}"

    # Counters
    pdf_count = img_count = v2_count = mpd_count = m3u8_count = yt_count = drm_count = zip_count = other_count = 0

    try:
        with open(x, "r", encoding='utf-8') as f:
            content = f.read()
        content = content.split("\n")
        content = [line.strip() for line in content if line.strip()]
        links = []
        for i in content:
            if "://" in i:
                parts = i.split("://", 1)
                if len(parts) == 2:
                    name = parts[0]
                    url = parts[1]
                    links.append([name, url])
                    if ".pdf" in url: pdf_count += 1
                    elif url.endswith((".png", ".jpeg", ".jpg")): img_count += 1
                    elif "v2" in url: v2_count += 1
                    elif "mpd" in url: mpd_count += 1
                    elif "m3u8" in url: m3u8_count += 1
                    elif "drm" in url: drm_count += 1
                    elif "youtu" in url: yt_count += 1
                    elif "zip" in url: zip_count += 1
                    else: other_count += 1
    except Exception as e:
        await m.reply_text(f"Error reading file: {e}")
        os.remove(x)
        return

    await editable.edit(
        f"**Total links: {len(links)}**\n"
        f"PDF: {pdf_count}   IMG: {img_count}   V2: {v2_count}\n"
        f"ZIP: {zip_count}   DRM: {drm_count}   M3U8: {m3u8_count}\n"
        f"MPD: {mpd_count}   YT: {yt_count}\n"
        f"Others: {other_count}\n\n"
        f"Send Index ID between 1-{len(links)}:"
    )

    chat_id = editable.chat.id
    timeout_duration = 3 if auto_flags.get(chat_id) else 20
    try:
        input0: Message = await bot.listen(editable.chat.id, timeout=timeout_duration)
        raw_text = input0.text
        await input0.delete(True)
    except asyncio.TimeoutError:
        raw_text = '1'

    if int(raw_text) > len(links):
        await editable.edit(f"Enter number in range 1-{len(links)}")
        return

    # Batch Name
    await editable.edit("1. Enter Batch Name\n2. Send /d for default")
    try:
        input1: Message = await bot.listen(editable.chat.id, timeout=timeout_duration)
        raw_text0 = input1.text
        await input1.delete(True)
    except asyncio.TimeoutError:
        raw_text0 = '/d'
    b_name = file_name.replace('_', ' ') if raw_text0 == '/d' else raw_text0

    # Resolution
    await editable.edit("Enter resolution:\n144/240/360/480/720/1080")
    try:
        input2: Message = await bot.listen(editable.chat.id, timeout=timeout_duration)
        raw_text2 = input2.text
        await input2.delete(True)
    except asyncio.TimeoutError:
        raw_text2 = '480'
    try:
        res_map = {"144":"256x144","240":"426x240","360":"640x360","480":"854x480","720":"1280x720","1080":"1920x1080"}
        res = res_map.get(raw_text2, "UN")
    except:
        res = "UN"

    # Watermark
    await editable.edit("Send watermark text or /d for none")
    try:
        inputx: Message = await bot.listen(editable.chat.id, timeout=timeout_duration)
        raw_textx = inputx.text
        await inputx.delete(True)
    except asyncio.TimeoutError:
        raw_textx = '/d'
    global watermark
    watermark = "/d" if raw_textx == '/d' else raw_textx

    # Credit
    await editable.edit("Send credit name or /d for default")
    try:
        input3: Message = await bot.listen(editable.chat.id, timeout=timeout_duration)
        raw_text3 = input3.text
        await input3.delete(True)
    except asyncio.TimeoutError:
        raw_text3 = '/d'
    if raw_text3 == '/d':
        CR = CREDIT
    elif "," in raw_text3:
        CR, PRENAME = raw_text3.split(",")
    else:
        CR = raw_text3

    # PW Token
    await editable.edit("Send PW token or /d")
    try:
        input4: Message = await bot.listen(editable.chat.id, timeout=timeout_duration)
        raw_text4 = input4.text
        await input4.delete(True)
    except asyncio.TimeoutError:
        raw_text4 = '/d'

    # Thumbnail
    await editable.edit("Send photo for thumbnail, /d for default, /skip to skip")
    thumb = "/d"
    try:
        input6 = await bot.listen(chat_id=m.chat.id, timeout=timeout_duration)
        if input6.photo:
            if not os.path.exists("downloads"):
                os.makedirs("downloads")
            temp_file = f"downloads/thumb_{m.from_user.id}.jpg"
            try:
                await bot.download_media(message=input6.photo, file_name=temp_file)
                thumb = temp_file
                await editable.edit("✅ Custom thumbnail saved")
                await asyncio.sleep(1)
            except Exception as e:
                print(f"Thumb error: {e}")
                thumb = "/d"
        elif input6.text:
            if input6.text == "/d":
                thumb = "/d"
            elif input6.text == "/skip":
                thumb = "no"
            else:
                thumb = "/d"
        await input6.delete(True)
    except asyncio.TimeoutError:
        thumb = "/d"
    except Exception as e:
        print(f"Thumb handling error: {e}")
        thumb = "/d"

    # Channel ID
    await editable.edit("Send Channel ID or /d for current chat")
    try:
        input7: Message = await bot.listen(editable.chat.id, timeout=timeout_duration)
        raw_text7 = input7.text
        await input7.delete(True)
    except asyncio.TimeoutError:
        raw_text7 = '/d'

    if raw_text7 == '/d':
        channel_id = m.chat.id
    else:
        channel_id = int(raw_text7)

    await editable.delete()

    failed_count = 0
    count = int(raw_text)
    arg = int(raw_text)

    # Main loop
    try:
        for i in range(arg-1, len(links)):
            Vxy = links[i][1].replace("file/d/","uc?export=download&id=").replace("www.youtube-nocookie.com/embed", "youtu.be").replace("?modestbranding=1", "").replace("/view?usp=sharing","")
            url = "https://" + Vxy
            link0 = "https://" + Vxy

            name1 = links[i][0].replace("(", "[").replace(")", "]").replace("_", "").replace("\t", "").replace(":", "").replace("/", "").replace("+", "").replace("#", "").replace("|", "").replace("@", "").replace("*", "").replace(".", "").replace("https", "").replace("http", "").strip()
            if "," in raw_text3:
                name = f'{PRENAME} {name1[:60]}'
            else:
                name = f'{name1[:60]}'

            # ========== AUTO GROUPING ==========
            user_settings = get_user_settings(m.from_user.id, bot_username)
            if user_settings.get("auto_grouping", False):
                group_chat_id = db.get_group_for_file(m.from_user.id, name1, bot_username)
                if group_chat_id:
                    channel_id = group_chat_id
            # ===================================

            # URL transformations (same as original code)
            if "visionias" in url:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers={'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9', 'Accept-Language': 'en-US,en;q=0.9', 'Cache-Control': 'no-cache', 'Connection': 'keep-alive', 'Pragma': 'no-cache', 'Referer': 'http://www.visionias.in/', 'Sec-Fetch-Dest': 'iframe', 'Sec-Fetch-Mode': 'navigate', 'Sec-Fetch-Site': 'cross-site', 'Upgrade-Insecure-Requests': '1', 'User-Agent': 'Mozilla/5.0 (Linux; Android 12; RMX2121) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36', 'sec-ch-ua': '"Chromium";v="107", "Not=A?Brand";v="24"', 'sec-ch-ua-mobile': '?1', 'sec-ch-ua-platform': '"Android"',}) as resp:
                        text = await resp.text()
                        url = re.search(r"(https://.*?playlist.m3u8.*?)\"", text).group(1)

            if "acecwply" in url:
                cmd = f'yt-dlp -o "{name}.%(ext)s" -f "bestvideo[height<={raw_text2}]+bestaudio" --hls-prefer-ffmpeg --no-keep-video --remux-video mkv --no-warning "{url}"'
            elif "https://static-trans-v1.classx.co.in" in url or "https://static-trans-v2.classx.co.in" in url:
                base_with_params, signature = url.split("*")
                base_clean = base_with_params.split(".mkv")[0] + ".mkv"
                if "static-trans-v1.classx.co.in" in url:
                    base_clean = base_clean.replace("https://static-trans-v1.classx.co.in", "https://appx-transcoded-videos-mcdn.akamai.net.in")
                elif "static-trans-v2.classx.co.in" in url:
                    base_clean = base_clean.replace("https://static-trans-v2.classx.co.in", "https://transcoded-videos-v2.classx.co.in")
                url = f"{base_clean}*{signature}"
            elif "https://static-rec.classx.co.in/drm/" in url:
                base_with_params, signature = url.split("*")
                base_clean = base_with_params.split("?")[0]
                base_clean = base_clean.replace("https://static-rec.classx.co.in", "https://appx-recordings-mcdn.akamai.net.in")
                url = f"{base_clean}*{signature}"
            elif "https://static-wsb.classx.co.in/" in url:
                clean_url = url.split("?")[0]
                clean_url = clean_url.replace("https://static-wsb.classx.co.in", "https://appx-wsb-gcp-mcdn.akamai.net.in")
                url = clean_url
            elif "https://static-db.classx.co.in/" in url:
                if "*" in url:
                    base_url, key = url.split("*", 1)
                    base_url = base_url.split("?")[0]
                    base_url = base_url.replace("https://static-db.classx.co.in", "https://appxcontent.kaxa.in")
                    url = f"{base_url}*{key}"
                else:
                    base_url = url.split("?")[0]
                    url = base_url.replace("https://static-db.classx.co.in", "https://appxcontent.kaxa.in")
            elif "https://static-db-v2.classx.co.in/" in url:
                if "*" in url:
                    base_url, key = url.split("*", 1)
                    base_url = base_url.split("?")[0]
                    base_url = base_url.replace("https://static-db-v2.classx.co.in", "https://appx-content-v2.classx.co.in")
                    url = f"{base_url}*{key}"
                else:
                    base_url = url.split("?")[0]
                    url = base_url.replace("https://static-db-v2.classx.co.in", "https://appx-content-v2.classx.co.in")
            elif "https://cpvod.testbook.com/" in url or "classplusapp.com/drm/" in url:
                url = url.replace("https://cpvod.testbook.com/","https://media-cdn.classplusapp.com/drm/")
                url = f"https://covercel.vercel.app/extract_keys?url={url}@bots_updatee&user_id=7793257011"
                mpd, keys = helper.get_mps_and_keys(url)
                url = mpd
                keys_string = " ".join([f"--key {key}" for key in keys])
            elif "classplusapp" in url:
                signed_api = f"https://covercel.vercel.app/extract_keys?url={url}@bots_updatee&user_id=7793257011"
                response = requests.get(signed_api, timeout=40)
                url = response.json()['url']
            elif "tencdn.classplusapp" in url:
                headers = {'host': 'api.classplusapp.com', 'x-access-token': f'{raw_text4}', 'accept-language': 'EN', 'api-version': '18', 'app-version': '1.4.73.2', 'build-number': '35', 'connection': 'Keep-Alive', 'content-type': 'application/json', 'device-details': 'Xiaomi_Redmi 7_SDK-32', 'device-id': 'c28d3cb16bbdac01', 'region': 'IN', 'user-agent': 'Mobile-Android', 'webengage-luid': '00000187-6fe4-5d41-a530-26186858be4c', 'accept-encoding': 'gzip'}
                params = {"url": f"{url}"}
                response = requests.get('https://api.classplusapp.com/cams/uploader/video/jw-signed-url', headers=headers, params=params)
                url = response.json()['url']
            elif 'videos.classplusapp' in url:
                url = requests.get(f'https://api.classplusapp.com/cams/uploader/video/jw-signed-url?url={url}', headers={'x-access-token': f'{raw_text4}'}).json()['url']
            elif 'media-cdn.classplusapp.com' in url or 'media-cdn-alisg.classplusapp.com' in url or 'media-cdn-a.classplusapp.com' in url:
                headers = {'host': 'api.classplusapp.com', 'x-access-token': f'{raw_text4}', 'accept-language': 'EN', 'api-version': '18', 'app-version': '1.4.73.2', 'build-number': '35', 'connection': 'Keep-Alive', 'content-type': 'application/json', 'device-details': 'Xiaomi_Redmi 7_SDK-32', 'device-id': 'c28d3cb16bbdac01', 'region': 'IN', 'user-agent': 'Mobile-Android', 'webengage-luid': '00000187-6fe4-5d41-a530-26186858be4c', 'accept-encoding': 'gzip'}
                params = {"url": f"{url}"}
                response = requests.get('https://api.classplusapp.com/cams/uploader/video/jw-signed-url', headers=headers, params=params)
                url = response.json()['url']
            elif "childId" in url and "parentId" in url:
                url = f"https://anonymouspwplayer-0e5a3f512dec.herokuapp.com/pw?url={url}&token={raw_text4}"
            if "edge.api.brightcove.com" in url:
                bcov = f'bcov_auth={cwtoken}'
                url = url.split("bcov_auth")[0]+bcov
            elif "d1d34p8vz63oiq" in url or "sec1.pw.live" in url:
                url = f"https://anonymouspwplayer-b99f57957198.herokuapp.com/pw?url={url}?token={raw_text4}"
            if ".pdf*" in url:
                url = f"https://dragoapi.vercel.app/pdf/{url}"
            elif 'encrypted.m' in url:
                appxkey = url.split('*')[1]
                url = url.split('*')[0]

            if "youtu" in url:
                ytf = f"bv*[height<={raw_text2}][ext=mp4]+ba[ext=m4a]/b[height<=?{raw_text2}]"
            elif "embed" in url:
                ytf = f"bestvideo[height<={raw_text2}]+bestaudio/best[height<={raw_text2}]"
            else:
                ytf = f"b[height<={raw_text2}]/bv[height<={raw_text2}]+ba/b/bv+ba"

            if "jw-prod" in url:
                cmd = f'yt-dlp -o "{name}.mp4" "{url}"'
            elif "webvideos.classplusapp." in url:
                cmd = f'yt-dlp --add-header "referer:https://web.classplusapp.com/" --add-header "x-cdn-tag:empty" -f "{ytf}" "{url}" -o "{name}.mp4"'
            elif "youtube.com" in url or "youtu.be" in url:
                cmd = f'yt-dlp --cookies youtube_cookies.txt -f "{ytf}" "{url}" -o "{name}".mp4'
            else:
                cmd = f'yt-dlp -f "{ytf}" "{url}" -o "{name}.mp4"'

            # Prepare captions
            current_ist = datetime.datetime.now(IST)
            date_str = current_ist.strftime('%d-%m-%Y')
            time_str = current_ist.strftime('%A, %d %B %Y • %I:%M %p')
            batch_blockquote = f'<blockquote>{b_name}</blockquote>'

            try:
                if "drive" in url:
                    ka = await helper.download(url, name)
                    ext_actual = "pdf"
                    cc = (
                        f"<b>🧭 Index ID:</b> {str(count).zfill(3)}\n\n"
                        f"<b>📎 Batch:</b> {batch_blockquote}\n\n"
                        f"<b>📥 Title:</b> {name1}\n\n"
                        f"[{date_str}]\n\n"
                        f"<b>📤 Extension:</b> {CR} .{ext_actual}\n"
                        f"<b>🧩 Resolution:</b> {res}\n\n"
                        f"<b>🍁 Uploaded By:</b> {CR}\n\n"
                        f"{time_str}"
                    )
                    await bot.send_document(chat_id=channel_id, document=ka, caption=cc)
                    count += 1
                    os.remove(ka)
                    continue

                elif ".pdf" in url:
                    if "cwmediabkt99" in url:
                        max_retries = 3
                        retry_delay = 4
                        success = False
                        for attempt in range(max_retries):
                            try:
                                await asyncio.sleep(retry_delay)
                                url = url.replace(" ", "%20")
                                scraper = cloudscraper.create_scraper()
                                response = scraper.get(url)
                                if response.status_code == 200:
                                    with open(f'{name}.pdf', 'wb') as file:
                                        file.write(response.content)
                                    ext_actual = "pdf"
                                    cc = (
                                        f"<b>🧭 Index ID:</b> {str(count).zfill(3)}\n\n"
                                        f"<b>📎 Batch:</b> {batch_blockquote}\n\n"
                                        f"<b>📥 Title:</b> {name1}\n\n"
                                        f"[{date_str}]\n\n"
                                        f"<b>📤 Extension:</b> {CR} .{ext_actual}\n"
                                        f"<b>🧩 Resolution:</b> {res}\n\n"
                                        f"<b>🍁 Uploaded By:</b> {CR}\n\n"
                                        f"{time_str}"
                                    )
                                    await bot.send_document(chat_id=channel_id, document=f'{name}.pdf', caption=cc)
                                    count += 1
                                    os.remove(f'{name}.pdf')
                                    success = True
                                    break
                            except Exception as e:
                                await asyncio.sleep(retry_delay)
                        if not success:
                            await m.reply_text(f"Failed to download PDF after retries.")
                            failed_count += 1
                            count += 1
                            continue
                    else:
                        cmd = f'yt-dlp -o "{name}.pdf" "{url}"'
                        download_cmd = f"{cmd} -R 25 --fragment-retries 25"
                        os.system(download_cmd)
                        ext_actual = "pdf"
                        cc = (
                            f"<b>🧭 Index ID:</b> {str(count).zfill(3)}\n\n"
                            f"<b>📎 Batch:</b> {batch_blockquote}\n\n"
                            f"<b>📥 Title:</b> {name1}\n\n"
                            f"[{date_str}]\n\n"
                            f"<b>📤 Extension:</b> {CR} .{ext_actual}\n"
                            f"<b>🧩 Resolution:</b> {res}\n\n"
                            f"<b>🍁 Uploaded By:</b> {CR}\n\n"
                            f"{time_str}"
                        )
                        await bot.send_document(chat_id=channel_id, document=f'{name}.pdf', caption=cc)
                        count += 1
                        os.remove(f'{name}.pdf')
                    continue

                elif ".ws" in url and url.endswith(".ws"):
                    await helper.pdf_download(f"{api_url}utkash-ws?url={url}&authorization={api_token}", f"{name}.html")
                    time.sleep(1)
                    ext_actual = "html"
                    cc = (
                        f"<b>🧭 Index ID:</b> {str(count).zfill(3)}\n\n"
                        f"<b>📎 Batch:</b> {batch_blockquote}\n\n"
                        f"<b>📥 Title:</b> {name1}\n\n"
                        f"[{date_str}]\n\n"
                        f"<b>📤 Extension:</b> {CR} .{ext_actual}\n"
                        f"<b>🧩 Resolution:</b> {res}\n\n"
                        f"<b>🍁 Uploaded By:</b> {CR}\n\n"
                        f"{time_str}"
                    )
                    await bot.send_document(chat_id=channel_id, document=f"{name}.html", caption=cc)
                    os.remove(f'{name}.html')
                    count += 1
                    continue

                elif any(ext in url for ext in [".jpg", ".jpeg", ".png"]):
                    ext_actual = url.split('.')[-1]
                    cmd = f'yt-dlp -o "{name}.{ext_actual}" "{url}"'
                    os.system(cmd)
                    cc = (
                        f"<b>🧭 Index ID:</b> {str(count).zfill(3)}\n\n"
                        f"<b>📎 Batch:</b> {batch_blockquote}\n\n"
                        f"<b>📥 Title:</b> {name1}\n\n"
                        f"[{date_str}]\n\n"
                        f"<b>📤 Extension:</b> {CR} .{ext_actual}\n"
                        f"<b>🧩 Resolution:</b> {res}\n\n"
                        f"<b>🍁 Uploaded By:</b> {CR}\n\n"
                        f"{time_str}"
                    )
                    await bot.send_photo(chat_id=channel_id, photo=f'{name}.{ext_actual}', caption=cc)
                    count += 1
                    os.remove(f'{name}.{ext_actual}')
                    continue

                elif any(ext in url for ext in [".mp3", ".wav", ".m4a"]):
                    ext_actual = url.split('.')[-1]
                    cmd = f'yt-dlp -x --audio-format {ext_actual} -o "{name}.{ext_actual}" "{url}"'
                    os.system(cmd)
                    cc = (
                        f"<b>🧭 Index ID:</b> {str(count).zfill(3)}\n\n"
                        f"<b>📎 Batch:</b> {batch_blockquote}\n\n"
                        f"<b>📥 Title:</b> {name1}\n\n"
                        f"[{date_str}]\n\n"
                        f"<b>📤 Extension:</b> {CR} .{ext_actual}\n"
                        f"<b>🧩 Resolution:</b> {res}\n\n"
                        f"<b>🍁 Uploaded By:</b> {CR}\n\n"
                        f"{time_str}"
                    )
                    await bot.send_document(chat_id=channel_id, document=f'{name}.{ext_actual}', caption=cc)
                    os.remove(f'{name}.{ext_actual}')
                    count += 1
                    continue

                elif 'encrypted.m' in url:
                    Show = f"<i><b>⚡ Video APPX Encrypted Downloading</b></i>\n<blockquote><b>{str(count).zfill(3)}) {name1}</b></blockquote>"
                    prog = await bot.send_message(channel_id, Show, disable_web_page_preview=True)
                    try:
                        res_file = await helper.download_and_decrypt_video(url, cmd, name, appxkey)
                        filename = res_file
                        await prog.delete(True)
                        if os.path.exists(filename):
                            ext_actual = os.path.splitext(filename)[1].lstrip('.')
                            cc = (
                                f"<b>🧭 Index ID:</b> {str(count).zfill(3)}\n\n"
                                f"<b>📎 Batch:</b> {batch_blockquote}\n\n"
                                f"<b>📥 Title:</b> {name1}\n\n"
                                f"[{date_str}]\n\n"
                                f"<b>📤 Extension:</b> {CR} .{ext_actual}\n"
                                f"<b>🧩 Resolution:</b> {res}\n\n"
                                f"<b>🍁 Uploaded By:</b> {CR}\n\n"
                                f"{time_str}"
                            )
                            await helper.send_vid(bot, m, cc, filename, thumb, name, prog, channel_id, watermark=watermark)
                            count += 1
                        else:
                            await bot.send_message(channel_id, f'⚠️ Failed to decrypt.')
                            failed_count += 1
                            count += 1
                            continue
                    except Exception as e:
                        await bot.send_message(channel_id, f'⚠️ Error: {str(e)}')
                        failed_count += 1
                        count += 1
                        continue

                elif 'drmcdni' in url or 'drm/wv' in url:
                    Show = f"<i><b>📥 Fast Video Downloading</b></i>\n<blockquote><b>{str(count).zfill(3)}) {name1}</b></blockquote>"
                    prog = await bot.send_message(channel_id, Show, disable_web_page_preview=True)
                    res_file = await helper.decrypt_and_merge_video(mpd, keys_string, path, name, raw_text2)
                    filename = res_file
                    await prog.delete(True)
                    ext_actual = os.path.splitext(filename)[1].lstrip('.')
                    cc = (
                        f"<b>🧭 Index ID:</b> {str(count).zfill(3)}\n\n"
                        f"<b>📎 Batch:</b> {batch_blockquote}\n\n"
                        f"<b>📥 Title:</b> {name1}\n\n"
                        f"[{date_str}]\n\n"
                        f"<b>📤 Extension:</b> {CR} .{ext_actual}\n"
                        f"<b>🧩 Resolution:</b> {res}\n\n"
                        f"<b>🍁 Uploaded By:</b> {CR}\n\n"
                        f"{time_str}"
                    )
                    await helper.send_vid(bot, m, cc, filename, thumb, name, prog, channel_id, watermark=watermark)
                    count += 1
                    await asyncio.sleep(1)
                    continue

                else:
                    Show = f"<i><b>📥 Fast Video Downloading</b></i>\n<blockquote><b>{str(count).zfill(3)}) {name1}</b></blockquote>"
                    prog = await bot.send_message(channel_id, Show, disable_web_page_preview=True)
                    res_file = await helper.download_video(url, cmd, name)
                    filename = res_file
                    await prog.delete(True)
                    ext_actual = os.path.splitext(filename)[1].lstrip('.')
                    cc = (
                        f"<b>🧭 Index ID:</b> {str(count).zfill(3)}\n\n"
                        f"<b>📎 Batch:</b> {batch_blockquote}\n\n"
                        f"<b>📥 Title:</b> {name1}\n\n"
                        f"[{date_str}]\n\n"
                        f"<b>📤 Extension:</b> {CR} .{ext_actual}\n"
                        f"<b>🧩 Resolution:</b> {res}\n\n"
                        f"<b>🍁 Uploaded By:</b> {CR}\n\n"
                        f"{time_str}"
                    )
                    await helper.send_vid(bot, m, cc, filename, thumb, name, prog, channel_id, watermark=watermark)
                    count += 1
                    time.sleep(1)

            except Exception as e:
                await bot.send_message(channel_id, f'⚠️ Download Failed: {str(e)}')
                failed_count += 1
                count += 1
                continue

    except Exception as e:
        await m.reply_text(str(e))
        time.sleep(2)

    # Summary
    success_count = len(links) - failed_count
    video_count = v2_count + mpd_count + m3u8_count + yt_count + drm_count + zip_count + other_count
    if raw_text7 == "/d":
        await bot.send_message(
            channel_id,
            f"<b>📬 Process Completed</b>\n\n"
            f"<blockquote><b>📚 Batch Name: {b_name}</b></blockquote>\n"
            f"Total URLs: {len(links)}\n"
            f"✅ Successful: {success_count}\n"
            f"❌ Failed: {failed_count}\n\n"
            f"🎞️ Videos: {video_count}\n"
            f"📑 PDFs: {pdf_count}\n"
            f"🖼️ Images: {img_count}\n\n"
            f"<i>Extracted by Krishna Bots 🤖</i>"
        )
    else:
        await bot.send_message(channel_id, f"✅ Completed: {b_name}\nTotal: {len(links)}, Success: {success_count}, Failed: {failed_count}")
        await bot.send_message(m.chat.id, f"✅ Task completed. Check your channel.")

# ========================= SINGLE LINK HANDLER =========================
@bot.on_message(filters.text & filters.private)
async def text_handler(bot: Client, m: Message):
    if m.from_user.is_bot:
        return
    # Ignore commands
    if m.text and m.text.startswith('/'):
        return
    links = m.text
    match = re.search(r'https?://\S+', links)
    if not match:
        # No URL found – silently ignore to avoid "Invalid link format"
        return
    link = match.group(0)

    editable = await m.reply_text("Processing link...")
    await m.delete()

    await editable.edit("Enter resolution (144/240/360/480/720/1080):")
    try:
        input2: Message = await bot.listen(editable.chat.id, timeout=20)
        raw_text2 = input2.text
        await input2.delete(True)
    except asyncio.TimeoutError:
        raw_text2 = '480'
    try:
        res_map = {"144":"256x144","240":"426x240","360":"640x360","480":"854x480","720":"1280x720","1080":"1920x1080"}
        res = res_map.get(raw_text2, "UN")
    except:
        res = "UN"

    raw_text4 = "working_token"
    thumb = "/d"
    count = 1
    channel_id = m.chat.id

    try:
        Vxy = link.replace("file/d/","uc?export=download&id=").replace("www.youtube-nocookie.com/embed", "youtu.be").replace("?modestbranding=1", "").replace("/view?usp=sharing","")
        url = Vxy
        name1 = links.replace("(", "[").replace(")", "]").replace("_", "").replace("\t", "").replace(":", "").replace("/", "").replace("+", "").replace("#", "").replace("|", "").replace("@", "").replace("*", "").replace(".", "").replace("https", "").replace("http", "").strip()
        name = f'{name1[:60]}'

        # Apply transformations (same as batch)
        if "visionias" in url:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers={'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9', 'Accept-Language': 'en-US,en;q=0.9', 'Cache-Control': 'no-cache', 'Connection': 'keep-alive', 'Pragma': 'no-cache', 'Referer': 'http://www.visionias.in/', 'Sec-Fetch-Dest': 'iframe', 'Sec-Fetch-Mode': 'navigate', 'Sec-Fetch-Site': 'cross-site', 'Upgrade-Insecure-Requests': '1', 'User-Agent': 'Mozilla/5.0 (Linux; Android 12; RMX2121) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36', 'sec-ch-ua': '"Chromium";v="107", "Not=A?Brand";v="24"', 'sec-ch-ua-mobile': '?1', 'sec-ch-ua-platform': '"Android"',}) as resp:
                    text = await resp.text()
                    url = re.search(r"(https://.*?playlist.m3u8.*?)\"", text).group(1)
        if "acecwply" in url:
            cmd = f'yt-dlp -o "{name}.%(ext)s" -f "bestvideo[height<={raw_text2}]+bestaudio" --hls-prefer-ffmpeg --no-keep-video --remux-video mkv --no-warning "{url}"'
        elif "https://static-trans-v1.classx.co.in" in url or "https://static-trans-v2.classx.co.in" in url:
            base_with_params, signature = url.split("*")
            base_clean = base_with_params.split(".mkv")[0] + ".mkv"
            if "static-trans-v1.classx.co.in" in url:
                base_clean = base_clean.replace("https://static-trans-v1.classx.co.in", "https://appx-transcoded-videos-mcdn.akamai.net.in")
            elif "static-trans-v2.classx.co.in" in url:
                base_clean = base_clean.replace("https://static-trans-v2.classx.co.in", "https://transcoded-videos-v2.classx.co.in")
            url = f"{base_clean}*{signature}"
        elif "https://static-rec.classx.co.in/drm/" in url:
            base_with_params, signature = url.split("*")
            base_clean = base_with_params.split("?")[0]
            base_clean = base_clean.replace("https://static-rec.classx.co.in", "https://appx-recordings-mcdn.akamai.net.in")
            url = f"{base_clean}*{signature}"
        elif "https://static-wsb.classx.co.in/" in url:
            clean_url = url.split("?")[0]
            clean_url = clean_url.replace("https://static-wsb.classx.co.in", "https://appx-wsb-gcp-mcdn.akamai.net.in")
            url = clean_url
        elif "https://static-db.classx.co.in/" in url:
            if "*" in url:
                base_url, key = url.split("*", 1)
                base_url = base_url.split("?")[0]
                base_url = base_url.replace("https://static-db.classx.co.in", "https://appxcontent.kaxa.in")
                url = f"{base_url}*{key}"
            else:
                base_url = url.split("?")[0]
                url = base_url.replace("https://static-db.classx.co.in", "https://appxcontent.kaxa.in")
        elif "https://static-db-v2.classx.co.in/" in url:
            if "*" in url:
                base_url, key = url.split("*", 1)
                base_url = base_url.split("?")[0]
                base_url = base_url.replace("https://static-db-v2.classx.co.in", "https://appx-content-v2.classx.co.in")
                url = f"{base_url}*{key}"
            else:
                base_url = url.split("?")[0]
                url = base_url.replace("https://static-db-v2.classx.co.in", "https://appx-content-v2.classx.co.in")
        elif "https://cpvod.testbook.com/" in url or "classplusapp.com/drm/" in url:
            url = url.replace("https://cpvod.testbook.com/","https://media-cdn.classplusapp.com/drm/")
            url = f"https://covercel.vercel.app/extract_keys?url={url}@bots_updatee&user_id=7793257011"
            mpd, keys = helper.get_mps_and_keys(url)
            url = mpd
            keys_string = " ".join([f"--key {key}" for key in keys])
        elif "classplusapp" in url:
            signed_api = f"https://covercel.vercel.app/extract_keys?url={url}@bots_updatee&user_id=7793257011"
            response = requests.get(signed_api, timeout=40)
            url = response.json()['url']
        elif "tencdn.classplusapp" in url:
            headers = {'host': 'api.classplusapp.com', 'x-access-token': f'{raw_text4}', 'accept-language': 'EN', 'api-version': '18', 'app-version': '1.4.73.2', 'build-number': '35', 'connection': 'Keep-Alive', 'content-type': 'application/json', 'device-details': 'Xiaomi_Redmi 7_SDK-32', 'device-id': 'c28d3cb16bbdac01', 'region': 'IN', 'user-agent': 'Mobile-Android', 'webengage-luid': '00000187-6fe4-5d41-a530-26186858be4c', 'accept-encoding': 'gzip'}
            params = {"url": f"{url}"}
            response = requests.get('https://api.classplusapp.com/cams/uploader/video/jw-signed-url', headers=headers, params=params)
            url = response.json()['url']
        elif 'videos.classplusapp' in url:
            url = requests.get(f'https://api.classplusapp.com/cams/uploader/video/jw-signed-url?url={url}', headers={'x-access-token': f'{raw_text4}'}).json()['url']
        elif 'media-cdn.classplusapp.com' in url or 'media-cdn-alisg.classplusapp.com' in url or 'media-cdn-a.classplusapp.com' in url:
            headers = {'host': 'api.classplusapp.com', 'x-access-token': f'{raw_text4}', 'accept-language': 'EN', 'api-version': '18', 'app-version': '1.4.73.2', 'build-number': '35', 'connection': 'Keep-Alive', 'content-type': 'application/json', 'device-details': 'Xiaomi_Redmi 7_SDK-32', 'device-id': 'c28d3cb16bbdac01', 'region': 'IN', 'user-agent': 'Mobile-Android', 'webengage-luid': '00000187-6fe4-5d41-a530-26186858be4c', 'accept-encoding': 'gzip'}
            params = {"url": f"{url}"}
            response = requests.get('https://api.classplusapp.com/cams/uploader/video/jw-signed-url', headers=headers, params=params)
            url = response.json()['url']
        elif "childId" in url and "parentId" in url:
            url = f"https://anonymouspwplayer-0e5a3f512dec.herokuapp.com/pw?url={url}&token={raw_text4}"
        if "edge.api.brightcove.com" in url:
            bcov = f'bcov_auth={cwtoken}'
            url = url.split("bcov_auth")[0]+bcov
        elif "d1d34p8vz63oiq" in url or "sec1.pw.live" in url:
            url = f"https://anonymouspwplayer-b99f57957198.herokuapp.com/pw?url={url}?token={raw_text4}"
        if ".pdf*" in url:
            url = f"https://dragoapi.vercel.app/pdf/{url}"
        elif 'encrypted.m' in url:
            appxkey = url.split('*')[1]
            url = url.split('*')[0]

        if "youtu" in url:
            ytf = f"bv*[height<={raw_text2}][ext=mp4]+ba[ext=m4a]/b[height<=?{raw_text2}]"
        elif "embed" in url:
            ytf = f"bestvideo[height<={raw_text2}]+bestaudio/best[height<={raw_text2}]"
        else:
            ytf = f"b[height<={raw_text2}]/bv[height<={raw_text2}]+ba/b/bv+ba"

        if "jw-prod" in url:
            cmd = f'yt-dlp -o "{name}.mp4" "{url}"'
        elif "webvideos.classplusapp." in url:
            cmd = f'yt-dlp --add-header "referer:https://web.classplusapp.com/" --add-header "x-cdn-tag:empty" -f "{ytf}" "{url}" -o "{name}.mp4"'
        elif "youtube.com" in url or "youtu.be" in url:
            cmd = f'yt-dlp --cookies youtube_cookies.txt -f "{ytf}" "{url}" -o "{name}".mp4'
        else:
            cmd = f'yt-dlp -f "{ytf}" "{url}" -o "{name}.mp4"'

        # Download and send
        current_ist = datetime.datetime.now(IST)
        date_str = current_ist.strftime('%d-%m-%Y')
        time_str = current_ist.strftime('%A, %d %B %Y • %I:%M %p')
        single_batch = '<blockquote>Single Video</blockquote>'

        # Direct download using helper
        res_file = await helper.download_video(url, cmd, name)
        if os.path.exists(res_file):
            ext_actual = os.path.splitext(res_file)[1].lstrip('.')
            cc = (
                f"<b>🧭 Index ID:</b> 001\n\n"
                f"<b>📎 Batch:</b> {single_batch}\n\n"
                f"<b>📥 Title:</b> {name1}\n\n"
                f"[{date_str}]\n\n"
                f"<b>📤 Extension:</b> {CREDIT} .{ext_actual}\n"
                f"<b>🧩 Resolution:</b> {res}\n\n"
                f"<b>🍁 Uploaded By:</b> {CREDIT}\n\n"
                f"{time_str}"
            )
            await helper.send_vid(bot, m, cc, res_file, thumb, name, None, channel_id, watermark=watermark)
        else:
            await m.reply_text("Download failed.")

    except Exception as e:
        await m.reply_text(f"Error: {str(e)}")

# ========================= OTHER FUNCTIONS =========================
def notify_owner():
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": OWNER_ID, "text": "Bot Is Live Now 🤖"})
    except:
        pass

def reset_and_set_commands():
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/setMyCommands"
        requests.post(url, json={"commands": []})
        commands = [
            {"command": "start", "description": "✅ Check if bot is alive"},
            {"command": "drm", "description": "📄 Upload a .txt file"},
            {"command": "stop", "description": "⏹ Terminate ongoing process"},
            {"command": "cookies", "description": "🍪 Upload YouTube cookies"},
            {"command": "t2h", "description": "📑 → 🌐 HTML converter"},
            {"command": "t2t", "description": "📝 Text → .txt generator"},
            {"command": "id", "description": "🆔 Get your user ID"},
            {"command": "setting", "description": "⚙️ Customize bot settings"},
            {"command": "add", "description": "▶️ Add Auth"},
            {"command": "remove", "description": "⏸️ Remove Auth"},
            {"command": "users", "description": "👨‍👨‍👧‍👦 All Users"},
        ]
        requests.post(url, json={"commands": commands})
    except:
        pass

if __name__ == "__main__":
    reset_and_set_commands()
    notify_owner()
    bot.run()

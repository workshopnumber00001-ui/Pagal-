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
import threading
import asyncio
import io
from base64 import b64encode, b64decode
from subprocess import getstatusoutput
from typing import Optional, Dict, List, Union
from pathlib import Path

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
import schedule
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

# ===================== LOG CHANNEL CONFIG =====================
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", str(OWNER_ID)))

# ===================== AUTO-UPLOADER CONFIGURATION =====================

AUTO_UPLOAD_ENABLED = os.getenv("AUTO_UPLOAD_ENABLED", "true").lower() == "true"
AUTO_UPLOAD_TIME = os.getenv("AUTO_UPLOAD_TIME", "09:00")
AUTO_UPLOAD_CHANNEL = int(os.getenv("AUTO_UPLOAD_CHANNEL", "-1003692273087"))
AUTO_UPLOAD_BATCH_IDS = os.getenv("AUTO_UPLOAD_BATCH_IDS", "").split(",")
AUTO_UPLOAD_INTERVAL_HOURS = int(os.getenv("AUTO_UPLOAD_INTERVAL_HOURS", "24"))
AUTO_UPLOAD_HISTORY_FILE = os.getenv("AUTO_UPLOAD_HISTORY_FILE", "upload_history.json")

# ===================== AUTO-UPLOADER API CONFIG =====================

API_BASE = os.getenv("API_BASE", "https://backend.multistreaming.site/api")
CW_ALL_BATCHES = os.getenv("CW_ALL_BATCHES", "https://cw-ut-apis-e37c22944d2f.herokuapp.com/api/batches")
CW_BATCH_API = os.getenv("CW_BATCH_API", "https://cw-api-website.vercel.app/batch/{}")
CW_TOPIC_API = os.getenv("CW_TOPIC_API", "https://cw-api-website.vercel.app/batch?batchid={}&topicid={}")
CW_VIDEO_API = os.getenv("CW_VIDEO_API", "https://cw-vid-virid.vercel.app/get_video_details?name={}")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# Set IST timezone
IST = pytz.timezone('Asia/Kolkata')

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

# ===================== AUTO-UPLOADER CLASS =====================

class AutoUploadManager:
    def __init__(self):
        self.is_running = False
        self.last_upload_time = None
        self.upload_history = self._load_history()
        self.scheduler_thread = None
        self.scheduler_running = False
        self.bot = None
        self._loop = None
        
    def _load_history(self):
        """Load upload history from file"""
        try:
            if os.path.exists(AUTO_UPLOAD_HISTORY_FILE):
                with open(AUTO_UPLOAD_HISTORY_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logging.warning(f"Could not load upload history: {e}")
        return []
    
    def _save_history(self):
        """Save upload history to file"""
        try:
            with open(AUTO_UPLOAD_HISTORY_FILE, 'w') as f:
                json.dump(self.upload_history, f, indent=2, default=str)
        except Exception as e:
            logging.error(f"Could not save upload history: {e}")
    
    async def _fetch_with_retry(self, session, url, retries=3, timeout=15):
        """Fetch with retry logic"""
        for attempt in range(retries):
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    logging.warning(f"Attempt {attempt+1}: {url} returned {resp.status}")
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logging.warning(f"Attempt {attempt+1} failed: {e}")
            await asyncio.sleep(2)
        return None
    
    async def extract_batch_content(self, batch_id: str, batch_name: str = None) -> tuple:
        """Extract content from a specific batch"""
        try:
            logging.info(f"Extracting content for batch: {batch_id}")
            
            async with aiohttp.ClientSession(headers=HEADERS) as session:
                # Try main API first
                batch_data = await self._fetch_with_retry(session, f"{API_BASE}/courses/{batch_id}/classes?populate=full")
                
                if batch_data:
                    topics = batch_data.get("data", {}).get("classes", [])
                    if topics:
                        batch_name = batch_data.get("data", {}).get("title") or batch_name or f"Batch_{batch_id}"
                        output = []
                        
                        for t in topics:
                            topic_name = t.get('topicName', 'General')
                            for cls in t.get("classes", []):
                                title = cls.get('title', 'Untitled').strip()
                                v_link = cls.get('class_link')
                                if v_link:
                                    output.append(f"🎥 [{topic_name}] {title} (VIDEO) : {v_link}")
                                for pdf in cls.get("classPdf", []):
                                    p_url = pdf.get("url") if isinstance(pdf, dict) else str(pdf)
                                    if p_url:
                                        output.append(f"📄 [{topic_name}] {title} (PDF) : {p_url}")
                        
                        if output:
                            return "\n".join(output), batch_name
                
                # Try CW API
                topics_data = await self._fetch_with_retry(session, CW_BATCH_API.format(batch_id))
                if topics_data:
                    batch_details = topics_data.get('data', topics_data) if isinstance(topics_data, dict) else topics_data
                    batch_name = batch_name or batch_details.get('batchName') or batch_details.get('name') or f"Batch_{batch_id}"
                    topics = batch_details.get('topics', []) if isinstance(batch_details, dict) else batch_details
                    
                    if isinstance(topics, list) and topics:
                        output = []
                        for topic in topics:
                            if not isinstance(topic, dict):
                                continue
                            topic_name = topic.get('topicName') or topic.get('name') or 'Unnamed Topic'
                            topic_id = topic.get('topicId') or topic.get('id') or topic.get('_id')
                            
                            if not topic_id:
                                continue
                            
                            content_url = CW_TOPIC_API.format(batch_id, topic_id)
                            content_res = await self._fetch_with_retry(session, content_url, timeout=12)
                            
                            if content_res:
                                inner_data = content_res.get('data', content_res) if isinstance(content_res, dict) else content_res
                                raw_videos = inner_data.get('classes', []) or inner_data.get('videos', []) or inner_data.get('class', [])
                                raw_pdfs = inner_data.get('notes', []) or inner_data.get('pdfs', []) or inner_data.get('batch-notes', [])
                                
                                if raw_videos:
                                    for vid in raw_videos:
                                        if isinstance(vid, dict):
                                            vid_name = vid.get('title') or vid.get('videoName') or vid.get('name') or 'Video'
                                            raw_token = vid.get('video_url') or vid.get('videoLink') or vid.get('url') or vid.get('link')
                                            if raw_token:
                                                output.append(f"🎥 [{topic_name}] {vid_name} : {str(raw_token)}")
                                
                                if raw_pdfs:
                                    for pdf in raw_pdfs:
                                        if isinstance(pdf, dict):
                                            pdf_name = pdf.get('title') or pdf.get('pdfName') or pdf.get('name') or 'Document'
                                            pdf_url = pdf.get('download_url') or pdf.get('view_url') or pdf.get('pdfLink')
                                            if pdf_url:
                                                output.append(f"📄 [{topic_name}] {pdf_name} : {pdf_url}")
                        
                        if output:
                            return "\n".join(output), batch_name
                
                return None, "No content found in batch"
                
        except Exception as e:
            logging.error(f"Error extracting batch {batch_id}: {e}")
            return None, str(e)
    
    async def upload_batch_content(self, bot, batch_id: str, batch_name: str = None, target_channel: int = None) -> tuple:
        """Extract and upload batch content to channel"""
        try:
            logging.info(f"Starting auto-upload for batch: {batch_id}")
            
            # Check if already uploaded today
            today = datetime.datetime.now(IST).date().isoformat()
            for record in self.upload_history:
                if record.get('batch_id') == batch_id and record.get('date') == today:
                    logging.info(f"Batch {batch_id} already uploaded today, skipping")
                    return True, "Already uploaded today"
            
            content, error = await self.extract_batch_content(batch_id, batch_name)
            
            if error or content is None:
                error_msg = f"❌ Auto-Upload Failed for batch {batch_id}: {error or 'No content found'}"
                logging.error(error_msg)
                return False, error_msg
            
            # Create file
            timestamp = datetime.datetime.now(IST).strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"batch_{batch_id}_{timestamp}.txt"
            
            # Add metadata header
            header = (
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⚡ Auto-Uploaded Batch Content\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📅 Uploaded: {datetime.datetime.now(IST).strftime('%A, %d %B %Y %I:%M %p')}\n"
                f"📛 Batch ID: {batch_id}\n"
                f"📦 Total Items: {len(content.split(chr(10)))}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            )
            
            full_content = header + content
            
            file_buffer = io.BytesIO(full_content.encode('utf-8'))
            file_buffer.name = filename
            
            channel = target_channel or AUTO_UPLOAD_CHANNEL
            
            # Send to channel
            caption = (
                f"✨ <b>AUTO-UPLOAD</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📛 <b>Batch ID:</b> {batch_id}\n"
                f"📦 <b>Items:</b> {len(content.split(chr(10)))}\n"
                f"📅 <b>Date:</b> {datetime.datetime.now(IST).strftime('%d-%m-%Y %I:%M %p')}\n"
                f"⏰ <b>Schedule:</b> Daily Auto-Upload\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⚡ {CREDIT}"
            )
            
            await bot.send_document(
                chat_id=channel,
                document=file_buffer,
                filename=filename,
                caption=caption,
                parse_mode="HTML"
            )
            
            # Record upload
            self.last_upload_time = datetime.datetime.now(IST)
            self.upload_history.append({
                'batch_id': batch_id,
                'date': today,
                'timestamp': self.last_upload_time.isoformat(),
                'filename': filename,
                'items_count': len(content.split(chr(10)))
            })
            self._save_history()
            
            logging.info(f"✅ Auto-upload completed for batch: {batch_id}")
            return True, f"Successfully uploaded batch {batch_id}"
            
        except Exception as e:
            logging.error(f"Auto-upload error for batch {batch_id}: {e}")
            return False, str(e)
    
    async def run_scheduled_upload(self):
        """Run the scheduled upload for all configured batches"""
        if not AUTO_UPLOAD_ENABLED:
            logging.info("Auto-upload is disabled")
            return
        
        if self.is_running:
            logging.info("Auto-upload already running, skipping...")
            return
        
        if self.bot is None:
            logging.error("Bot not set for auto-uploader")
            return
        
        self.is_running = True
        try:
            batch_ids = [bid.strip() for bid in AUTO_UPLOAD_BATCH_IDS if bid.strip()]
            
            if not batch_ids:
                logging.warning("No batch IDs configured for auto-upload")
                return
            
            results = []
            success_count = 0
            
            for batch_id in batch_ids:
                success, message = await self.upload_batch_content(self.bot, batch_id)
                if success:
                    success_count += 1
                results.append(f"• Batch {batch_id}: {'✅' if success else '❌'} {message}")
                await asyncio.sleep(2)
            
            # Send summary to log channel
            summary = (
                f"📊 <b>Auto-Upload Summary</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📅 {datetime.datetime.now(IST).strftime('%A, %d %B %Y')}\n"
                f"⏰ {datetime.datetime.now(IST).strftime('%I:%M %p')}\n"
                f"📊 Success: {success_count}/{len(batch_ids)}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                + "\n".join(results)
            )
            
            try:
                await self.bot.send_message(
                    chat_id=LOG_CHANNEL_ID,
                    text=summary,
                    parse_mode="HTML"
                )
            except Exception as e:
                logging.error(f"Failed to send summary: {e}")
            
        except Exception as e:
            logging.error(f"Auto-upload failed: {e}")
        finally:
            self.is_running = False
    
    def _run_async_upload(self):
        """Run async upload in event loop"""
        try:
            if self._loop is None:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
            
            self._loop.run_until_complete(self.run_scheduled_upload())
        except Exception as e:
            logging.error(f"Async upload failed: {e}")
    
    def start_scheduler(self, bot):
        """Start the scheduler in a separate thread"""
        if self.scheduler_running:
            return
        
        self.bot = bot
        
        def run_scheduler():
            # Schedule daily upload
            schedule.every().day.at(AUTO_UPLOAD_TIME).do(self._run_async_upload)
            
            # Also run every X hours if interval is less than 24
            if AUTO_UPLOAD_INTERVAL_HOURS < 24:
                schedule.every(AUTO_UPLOAD_INTERVAL_HOURS).hours.do(self._run_async_upload)
            
            self.scheduler_running = True
            logging.info(f"🔄 Auto-upload scheduler started. Daily at {AUTO_UPLOAD_TIME}")
            
            while self.scheduler_running:
                schedule.run_pending()
                time.sleep(60)
        
        self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        self.scheduler_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        logging.info("Auto-upload scheduler stopped")

# ===================== BOT COMMANDS =====================

@bot.on_message(filters.command("autoupload") & filters.private)
async def auto_upload_cmd(client: Client, message: Message):
    """Manually trigger auto-upload"""
    try:
        if not db.is_admin(message.from_user.id):
            await message.reply_text("⚠️ You are not authorized to use this command!")
            return
        
        if not hasattr(bot, 'auto_upload_manager'):
            await message.reply_text("❌ Auto-upload manager not initialized")
            return
        
        manager = bot.auto_upload_manager
        msg = await message.reply_text("⏳ Starting auto-upload manually...")
        
        await manager.run_scheduled_upload()
        
        await msg.edit_text(
            f"✅ <b>Auto-upload completed!</b>\n\n"
            f"📅 {datetime.datetime.now(IST).strftime('%A, %d %B %Y %I:%M %p')}\n"
            f"📤 Check channel for uploaded files",
            parse_mode="HTML"
        )
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")

@bot.on_message(filters.command("autouploadstatus") & filters.private)
async def auto_upload_status_cmd(client: Client, message: Message):
    """Check auto-upload status"""
    try:
        if not db.is_admin(message.from_user.id):
            await message.reply_text("⚠️ You are not authorized to use this command!")
            return
        
        if not hasattr(bot, 'auto_upload_manager'):
            await message.reply_text("❌ Auto-upload manager not initialized")
            return
        
        manager = bot.auto_upload_manager
        
        status_text = (
            f"📊 <b>Auto-Upload Status</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚙️ <b>Enabled:</b> {'✅ Yes' if AUTO_UPLOAD_ENABLED else '❌ No'}\n"
            f"⏰ <b>Schedule:</b> Daily at {AUTO_UPLOAD_TIME}\n"
            f"📊 <b>Interval:</b> {AUTO_UPLOAD_INTERVAL_HOURS} hours\n"
            f"📋 <b>Batch IDs:</b>\n"
            f"{chr(10).join(['  • ' + bid for bid in AUTO_UPLOAD_BATCH_IDS if bid.strip()]) or '  None configured'}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📤 <b>Last Upload:</b> {manager.last_upload_time.strftime('%d-%m-%Y %I:%M %p') if manager.last_upload_time else 'Never'}\n"
            f"📦 <b>Upload History:</b> {len(manager.upload_history)} batches\n"
            f"🔄 <b>Currently Running:</b> {'✅ Yes' if manager.is_running else '❌ No'}"
        )
        
        await message.reply_text(status_text, parse_mode="HTML")
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")

@bot.on_message(filters.command("autouploadconfig") & filters.private)
async def auto_upload_config_cmd(client: Client, message: Message):
    """Configure auto-upload settings"""
    try:
        if not db.is_admin(message.from_user.id):
            await message.reply_text("⚠️ You are not authorized to use this command!")
            return
        
        await message.reply_text(
            f"⚙️ <b>Auto-Upload Configuration</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"To configure auto-upload, set these environment variables:\n\n"
            f"• <code>AUTO_UPLOAD_ENABLED</code> = true/false\n"
            f"• <code>AUTO_UPLOAD_TIME</code> = HH:MM (e.g., 09:00)\n"
            f"• <code>AUTO_UPLOAD_CHANNEL</code> = Channel ID\n"
            f"• <code>AUTO_UPLOAD_BATCH_IDS</code> = comma,separated,ids\n"
            f"• <code>AUTO_UPLOAD_INTERVAL_HOURS</code> = 24\n\n"
            f"<b>Current Status:</b>\n"
            f"• Enabled: {AUTO_UPLOAD_ENABLED}\n"
            f"• Time: {AUTO_UPLOAD_TIME}\n"
            f"• Channel: {AUTO_UPLOAD_CHANNEL}\n"
            f"• Batches: {', '.join([bid for bid in AUTO_UPLOAD_BATCH_IDS if bid.strip()]) or 'None'}\n"
            f"• Interval: {AUTO_UPLOAD_INTERVAL_HOURS}h",
            parse_mode="HTML"
        )
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")

# ===================== SETTINGS SYSTEM =====================

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

# ===================== SETTINGS CALLBACK =====================

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

# ===================== BOT EVENTS =====================

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

# ===================== MAIN EXECUTION =====================

def notify_owner():
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": OWNER_ID, "text": "🤖 Bot Is Live Now with Auto-Uploader!"}
        )
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
            {"command": "autoupload", "description": "⏰ Manual auto-upload (Admin)"},
            {"command": "autouploadstatus", "description": "📊 Auto-upload status (Admin)"},
            {"command": "autouploadconfig", "description": "⚙️ Auto-upload config (Admin)"},
        ]
        requests.post(url, json={"commands": commands})
    except:
        pass

if __name__ == "__main__":
    logging.info("🚀 Starting Bot...")
    
    # Initialize auto-upload manager
    auto_upload_manager = AutoUploadManager()
    bot.auto_upload_manager = auto_upload_manager
    
    # Register clean handler
    register_clean_handler(bot)
    
    # Re-register auth commands
    bot.add_handler(MessageHandler(auth.add_user_cmd, filters.command("add") & filters.private))
    bot.add_handler(MessageHandler(auth.remove_user_cmd, filters.command("remove") & filters.private))
    bot.add_handler(MessageHandler(auth.list_users_cmd, filters.command("users") & filters.private))
    bot.add_handler(MessageHandler(auth.my_plan_cmd, filters.command("plan") & filters.private))
    
    reset_and_set_commands()
    notify_owner()
    
    # Start the auto-upload scheduler (non-blocking)
    if AUTO_UPLOAD_ENABLED:
        # Start scheduler in background thread
        auto_upload_manager.start_scheduler(bot)
        logging.info(f"🔄 Auto-uploader started. Daily at {AUTO_UPLOAD_TIME}")
        logging.info(f"📋 Batch IDs: {AUTO_UPLOAD_BATCH_IDS}")
        logging.info(f"📤 Upload Channel: {AUTO_UPLOAD_CHANNEL}")
    
    # Run the bot (this will block main thread)
    logging.info("🚀 Starting Pyrogram Client...")
    bot.run()

import telebot
from telebot import apihelper
import yt_dlp
import os
import time
import re
from flask import Flask
from threading import Thread

# --- 🔐 HIDDEN TOKEN ---
# Ensure you set 'BOT_TOKEN' in Render's Environment Variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# --- ⚙️ NETWORK CONFIGURATION ---
apihelper.ENABLE_MIDDLEWARE = True
apihelper.SESSION_TIME_TO_LIVE = 5 * 60 

bot = telebot.TeleBot(BOT_TOKEN)
BOT_START_TIME = time.time() + 2

# --- 🌐 KEEP ALIVE SERVER ---
app = Flask('')

@app.route('/')
def home():
    return "TikTok Bot is Running!"

def run_http():
    # Render assigns a port automatically via environment variables
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_http)
    t.start()

# ------------------------------------------

def download_video(url, unique_id):
    """Downloads TikTok video using yt-dlp with your cookies.txt."""
    filename = f"tiktok_{unique_id}.mp4"
    cookie_path = 'cookies.txt'
    
    ydl_opts = {
        'format': 'bestvideo[vcodec^=avc]+bestaudio[acodec^=mp4a]/best[ext=mp4]/best',
        'outtmpl': f"tiktok_{unique_id}.%(ext)s",
        'merge_output_format': 'mp4',
        'cookiefile': cookie_path if os.path.exists(cookie_path) else None,
        'postprocessors': [{'key': 'FFmpegVideoConvertor', 'preferedformat': 'mp4'}],
        'postprocessor_args': {'ffmpeg': ['-pix_fmt', 'yuv420p']},
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return {
                'path': filename,
                'width': info.get('width'),
                'height': info.get('height'),
                'duration': info.get('duration')
            }
    except Exception as e:
        print(f"Download Error: {e}")
        return None

def extract_clean_link(text):
    """Extracts TikTok URLs."""
    pattern = r'(https?://(?:www\.|vm\.|vt\.)?tiktok\.com/[^\s]+)'
    match = re.search(pattern, text)
    return match.group(1) if match else None

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.date < BOT_START_TIME: return

    text = message.text
    chat_id = message.chat.id
    unique_id = f"{chat_id}_{message.message_id}"

    if "tiktok.com" in text:
        clean_url = extract_clean_link(text)
        if not clean_url: return 

        try:
            bot.delete_message(chat_id, message.message_id)
            # --- 🔗 UPDATED LINK LINE ---
            bot.send_message(chat_id, f'🔗 <a href="{clean_url}">LINK</a>', parse_mode='HTML', disable_web_page_preview=True)
        except: pass 
        
        status_msg = bot.send_message(chat_id, "🧃")
        bot.send_chat_action(chat_id, 'upload_video')

        video_data = download_video(clean_url, unique_id)
        
        if video_data and os.path.exists(video_data['path']):
            with open(video_data['path'], 'rb') as video:
                bot.send_video(
                    chat_id, video, 
                    width=video_data.get('width'), height=video_data.get('height'),
                    duration=video_data.get('duration'), supports_streaming=True
                )
            
            # --- 〰️ SEPARATOR LINE ---
            bot.send_message(chat_id, "〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️")
            
            try: bot.delete_message(chat_id, status_msg.message_id)
            except: pass
            
            os.remove(video_data['path'])
        else:
            bot.edit_message_text("❌ Download failed.", chat_id, status_msg.message_id)

if __name__ == "__main__":
    keep_alive()
    print("TikTok Bot is starting on Render... ⚡")
    bot.infinity_polling(skip_pending=True)


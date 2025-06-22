import telebot
import requests
import os
from yt_dlp import YoutubeDL
import lyricsgenius
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# === TOKENS ===
BOT_TOKEN = "7712672910:AAGHmfSmmP_B2qjKkfTbbCNANTpQ_8l1IHc"
GENIUS_TOKEN = "JlWpgoCG1txhjhsXCLoZl7C0d5Dhhv7r2I84aJW5YoabPzX9QDEHWrsHsjFbt8e4"

bot = telebot.TeleBot(BOT_TOKEN)
genius = lyricsgenius.Genius(GENIUS_TOKEN)
genius.skip_non_songs = True
genius.excluded_terms = ["(Remix)", "(Live)"]

# === Footer ===
footer = "\n\n🤴🏻 𝐃𝐞𝐯𝐥𝐨𝐩𝐞𝐫 👨🏻‍💻 : @tera_paglu"

# === START ===
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🎵 Send me a song name and I'll give you Lyrics + MP3!" + footer)

# === MAIN SONG SEARCH ===
@bot.message_handler(func=lambda m: True)
def search_song(message):
    query = message.text
    bot.send_chat_action(message.chat.id, 'typing')

    try:
        # Genius Search
        song = genius.search_song(query)
        if not song:
            bot.send_message(message.chat.id, "❌ Song not found." + footer)
            return

        title = song.title
        artist = song.artist
        lyrics = song.lyrics
        cover = song.song_art_image_url

        # YouTube Search
        yt_search = f"https://www.youtube.com/results?search_query={query}+audio"
        yt_page = requests.get(yt_search).text
        video_id = yt_page.split('watch?v=')[1].split('"')[0]
        yt_link = f"https://www.youtube.com/watch?v={video_id}"

        # Download MP3
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'song.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True
        }

        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([yt_link])

        # Inline Buttons
        markup = InlineKeyboardMarkup()
        markup.row_width = 2
        markup.add(
            InlineKeyboardButton("🎧 Download MP3", callback_data="mp3"),
            InlineKeyboardButton("📄 View Full Lyrics", callback_data="lyrics"),
            InlineKeyboardButton("🔗 YouTube", url=yt_link),
            InlineKeyboardButton("🔁 Search Again", switch_inline_query_current_chat="")
        )

        caption = f"🎵 *{title}*\n👤 {artist}\n\n📝 *Lyrics Preview:*\n{lyrics[:400]}..." + footer
        bot.send_photo(message.chat.id, cover, caption=caption, parse_mode="Markdown", reply_markup=markup)

        with open("song_data.txt", "w", encoding="utf-8") as f:
            f.write(lyrics)
        with open("song_info.txt", "w", encoding="utf-8") as f:
            f.write(f"{title}|{artist}")

    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ Error: {str(e)}" + footer)

# === CALLBACK HANDLER ===
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "mp3":
        try:
            with open("song.mp3", "rb") as audio:
                with open("song_info.txt", "r") as f:
                    title, artist = f.read().split("|")
                bot.send_audio(call.message.chat.id, audio, title=title, performer=artist, caption=footer)
            os.remove("song.mp3")
        except:
            bot.send_message(call.message.chat.id, "❌ MP3 not found." + footer)

    elif call.data == "lyrics":
        try:
            with open("song_data.txt", "r", encoding="utf-8") as f:
                lyrics = f.read()
            for i in range(0, len(lyrics), 4090):
                bot.send_message(call.message.chat.id, lyrics[i:i+4090] + footer)
        except:
            bot.send_message(call.message.chat.id, "❌ Lyrics not found." + footer)

# === RUN BOT ===
print("🤖 Paglu Bot is Running...")
bot.polling()

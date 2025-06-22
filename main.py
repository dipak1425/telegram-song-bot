import telebot
import requests
import os
from bs4 import BeautifulSoup
from yt_dlp import YoutubeDL
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "7712672910:AAGHmfSmmP_B2qjKkfTbbCNANTpQ_8l1IHc"
bot = telebot.TeleBot(BOT_TOKEN)
footer = "\n\n🤴🏻 𝐃𝐞𝐯𝐥𝐨𝐩𝐞𝐫 👨🏻‍💻 : @tera_paglu"

def get_lyricsmint(song_name):
    try:
        search_url = f"https://www.google.com/search?q=site:lyricsmint.com+{song_name}"
        headers = {"User-Agent": "Mozilla/5.0"}
        page = requests.get(search_url, headers=headers).text
        link = page.split('/url?q=')[1].split('&')[0]
        html = requests.get(link, headers=headers).text
        soup = BeautifulSoup(html, "html.parser")
        lyrics = soup.find("div", class_="lyrics").get_text("\n").strip()
        return lyrics
    except:
        return None

def get_lyricsbogie(song_name):
    try:
        search_url = f"https://www.google.com/search?q=site:lyricsbogie.com+{song_name}"
        headers = {"User-Agent": "Mozilla/5.0"}
        page = requests.get(search_url, headers=headers).text
        link = page.split('/url?q=')[1].split('&')[0]
        html = requests.get(link, headers=headers).text
        soup = BeautifulSoup(html, "html.parser")
        lyrics = soup.find("div", class_="entry-content").get_text("\n").strip()
        return lyrics
    except:
        return None

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🎵 Send me a Bollywood song name and I’ll give you Lyrics + MP3!" + footer)

@bot.message_handler(func=lambda m: True)
def handle_song(message):
    query = message.text
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        lyrics = get_lyricsmint(query)
        if not lyrics:
            lyrics = get_lyricsbogie(query)
        if not lyrics:
            bot.send_message(message.chat.id, "❌ Lyrics not found." + footer)
            return

        # YouTube search
        yt_search = f"https://www.youtube.com/results?search_query={query}+audio"
        page = requests.get(yt_search).text
        video_id = page.split('watch?v=')[1].split('"')[0]
        yt_link = f"https://www.youtube.com/watch?v={video_id}"
        cover = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"

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

        # Buttons
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("🎧 Download MP3", callback_data="mp3"),
            InlineKeyboardButton("📄 View Full Lyrics", callback_data="lyrics"),
            InlineKeyboardButton("🔗 YouTube", url=yt_link)
        )

        preview = lyrics[:400] + "..." if len(lyrics) > 400 else lyrics
        caption = f"🎶 *{query.title()}*\n\n📝 *Lyrics Preview:*\n{preview}" + footer

        bot.send_photo(message.chat.id, photo=cover, caption=caption, parse_mode="Markdown", reply_markup=markup)

        with open("song_data.txt", "w", encoding="utf-8") as f:
            f.write(lyrics)
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ Error: {str(e)}" + footer)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data == "mp3":
        try:
            with open("song.mp3", "rb") as audio:
                bot.send_audio(call.message.chat.id, audio, caption=footer)
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

print("🎶 BabuLyricsBot Running with LyricsMint + LyricsBogie ❤️‍🔥")
bot.polling()
    

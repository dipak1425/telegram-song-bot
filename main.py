import telebot
import requests
import os
from bs4 import BeautifulSoup
from yt_dlp import YoutubeDL
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "7712672910:AAGHmfSmmP_B2qjKkfTbbCNANTpQ_8l1IHc"
bot = telebot.TeleBot(BOT_TOKEN)
footer = "\n\n🤴🏻 𝐃𝐞𝐯𝐥𝐨𝐩𝐞𝐫 👨🏻‍💻 : @tera_paglu"

def get_lyrics(song_name):
    query = song_name.replace(" ", "+")
    search_url = f"https://search.azlyrics.com/search.php?q={query}"
    res = requests.get(search_url)
    soup = BeautifulSoup(res.text, "html.parser")
    link_tag = soup.select_one("td.text-left a")
    if not link_tag:
        return None
    lyrics_url = link_tag['href']
    lyrics_res = requests.get(lyrics_url)
    lyrics_soup = BeautifulSoup(lyrics_res.text, "html.parser")
    divs = lyrics_soup.find_all("div", class_=False)
    lyrics = divs[0].get_text("\n").strip() if divs else "Lyrics not found."
    return lyrics

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🎵 Send me a song name and I’ll give you Lyrics + MP3!" + footer)

@bot.message_handler(func=lambda m: True)
def handle_song(message):
    query = message.text
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        # Get lyrics
        lyrics = get_lyrics(query)
        if not lyrics:
            bot.send_message(message.chat.id, "❌ Lyrics not found." + footer)
            return

        # Get YouTube Link
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

print("🤖 Paglu Bot is Running with AZLyrics...")
bot.polling()
        

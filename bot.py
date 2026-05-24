from telegram import Update
from telegram.ext import MessageHandler, filters
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv
import requests
import os
import re
import yt_dlp
import asyncio
from faster_whisper import WhisperModel


model = WhisperModel("tiny")

queue = []
is_playing = False

play_lock = asyncio.Lock() # The Lock prevents this by making Command 2 wait until Command 1 has finished checking AND set is_playing = True.


load_dotenv()


async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'Hello {update.effective_user.first_name}')

async def echo(update, context):
    text = update.message.text

    if text == "idris":
        await update.message.reply_text("idris online...")
    else:
        await update.message.reply_text(f"you said: {text}")


def download_audio(url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': 'audio',
        'cookiefile': 'cookies.txt',      # ← Use this
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


async def process_song(update ,song_name):
        await update.message.reply_text("🔍 scanning the grid...")
        await asyncio.sleep(2)
        response = requests.get(f'https://www.youtube.com/results?search_query={song_name}')
        await update.message.reply_text("🎯 target acquired...")
        await asyncio.sleep(2)
        match = re.search(r'watch\?v=([a-zA-Z0-9_-]+)', response.text)
        await update.message.reply_text("⚡ extracting audio signature...")
        await asyncio.sleep(2)
        await asyncio.to_thread(download_audio,f'https://www.youtube.com/watch?v={match.group(1)}')  # This says "run download_audio in a separate thread, so the event loop stays free." Does that make sense?
        await update.message.reply_text("📡 downloading to local core...")                           # Wrong: you cook the food yourself, then hand the plate to the chef,  Right: you hand the recipe to the chef, let them cook it, to_thread is the chef. It needs the recipe (function), not the cooked food (result).
        await asyncio.sleep(2)
        await update.message.reply_audio(open('audio.mp3', 'rb'), read_timeout=60, write_timeout=60)
        await update.message.reply_text("🎵 enjoy boss.")

async def voice_handler(update, context):
    global is_playing
    file_id = update.message.voice.file_id  # this is the voice tag or the coat check ticket
    file = await context.bot.get_file(file_id) #this gets the audio files id like a coat check counter giving a token to collect the coat later
    
    await file.download_to_drive("voice.ogg") # this uses the file id to locally downold the audio to system
    
    segments, info = model.transcribe("voice.ogg") # Faster-Whisper splits audio into time chunks. Each chunk is a segment.


    texts = []
    for segment in segments:
        texts.append(segment.text) # This gives you just the text & not the whole object like <Segment object> only the text part like  "hey play"
    text = " ".join(texts)
  
    words = text.split()

    lower_word = []
    for i in words:
        i.strip(".,!?")
        lower_word.append(i.lower().strip(".,!?"))
        
    
    
    


    print(f"Transcribed: {text}")
    print(f"Words: {words}")

    if "play" in lower_word:
        play_index  = lower_word.index('play')
        song_name = "+".join(words[play_index + 1:])
        if is_playing is True:
            queue.append(song_name)
            await update.message.reply_text("🎵 added to queue!")

            
        else:
            is_playing = True
            await process_song(update, song_name)             #   ---b.)            |
            while queue != []: # check if queue has song in it, if it has move down v
                song_name = queue.pop(0)
                await process_song(update, song_name) # --- a.)
            is_playing = False  # if is_playing is inside while loop once song starts playing from (a) it sets is_playing to false and next song will start playing from (b) same time song is playing from (a)
            
    else:
        await update.message.reply_text(f'did you say "{text}" boss?')


async def play (update,context):
    global is_playing

    if context.args == []:
        await update.message.reply_text("broo like a real song name....")
    else :
        context.args.append("music")
        song_name = "+".join(context.args)

        async with play_lock:  # means "grab the key, do your thing, release the key." While one command holds the key, all others wait outside.
        
            if is_playing is True:
                queue.append(song_name)
                await update.message.reply_text("🎵 added to queue!")
                return     # return says "we're done here, stop.
                           # Without return, after adding to queue and showing the message, Python would continue down and hit await process_song — starting a second song even though one is already playing.
            else:
                print(f"is_playing value: {is_playing}")
                is_playing = True                         # If the lock wraps the whole download too, Command 2 has to wait outside the bathroom the entire time song 1 is downloading — maybe 30 seconds! It can never even add itself to the queue.
                                                          #The lock should be like a quick "grab the key, check, set, release" — not "hold the key the whole time."
        await process_song(update, song_name)             #   ---b.)            |
        while queue != []: # check if queue has song in it, if it has move down v
            song_name = queue.pop(0)
            await process_song(update, song_name) # --- a.)
        is_playing = False  # if is_playing is inside while loop once song starts playing from (a) it sets is_playing to false and next song will start playing from (b) same time song is playing from (a)
        
            
app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()

app.add_handler(MessageHandler(filters.VOICE & ~filters.COMMAND, voice_handler))

app.add_handler(CommandHandler("play", play))

app.run_polling()
            

# /play billie jean by michael jackson
# /play blinding lights by the weekend
# /play thriller by michael jackson






# .venv\Scripts\activate
#  python bot.py
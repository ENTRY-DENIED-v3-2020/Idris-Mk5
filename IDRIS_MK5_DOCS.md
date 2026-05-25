# Idris Music Bot — Mark 5 Documentation

## What's New in Mark 5
- Replaced heavy Whisper with **Faster-Whisper** (lightweight, Pi-friendly)
- Fixed voice transcription case sensitivity issue
- Added punctuation stripping from transcribed words
- Added `try/finally` to ensure `is_playing` always resets
- Added upload timeouts to prevent silent failures
- Better error feedback — bot tells you what it heard

---

## Key Concepts

### Why Faster-Whisper?
Regular Whisper needed ~2GB of space and RAM — too heavy for Pi 3B+.
Faster-Whisper uses **quantization** (compressing the model) to run with much less memory.

We use the `tiny` model — smallest and fastest, but less accurate:
```python
from faster_whisper import WhisperModel
model = WhisperModel("tiny")
```
Available sizes: tiny → base → small → medium → large. Bigger = more accurate but heavier.

**Note:** Expect occasional transcription errors with `tiny`. It works for most songs but may mishear uncommon names.

---

### How Faster-Whisper Returns Text (Segments)
Unlike regular Whisper which returns one full string, Faster-Whisper splits audio into time-based chunks called **segments**.

Think of it like a live subtitler breaking a speech into lines as they go, rather than typing the whole thing at once.

```python
segments, info = model.transcribe("voice.ogg")

texts = []
for segment in segments:
    texts.append(segment.text)   # extract text from each chunk
text = " ".join(texts)           # join all chunks into one string
words = text.split()             # split into individual words
```

- `segment` → one time chunk of audio
- `segment.text` → the text string inside that chunk
- `text` → your final joined sentence (a plain string variable)

---

### Lowercase Fix — Case Sensitivity Problem
**Problem:** Faster-Whisper sometimes capitalizes words — e.g. `"Play"` instead of `"play"`. The `if "play" in words` check is case-sensitive, so `"Play"` would fail and the bot would say "I didn't catch that."

**Fix:** Convert all words to lowercase before checking:
```python
lower_word = []
for i in words:
    lower_word.append(i.lower().strip(".,!?"))
```

Then check `lower_word` instead of `words`:
```python
if "play" in lower_word:
    play_index = lower_word.index('play')
    song_name = "+".join(words[play_index + 1:])  # keep original words for search
```

Note: `words` is still used for `song_name` — you want original capitalization when searching YouTube.

---

### Punctuation Stripping
**Problem:** Whisper sometimes adds punctuation — e.g. `"Play,"` or `"Adams."`. This breaks the `"play"` check.

**Fix:** `.strip(".,!?")` removes punctuation from the edges of each word:
```python
i.lower().strip(".,!?")
```

Chain it with `.lower()` in one line — clean and efficient.

---

### f-strings
f-strings let you embed variables directly inside a string using `{}`:
```python
f'did you say "{text}" boss?'
```
The `f` prefix tells Python to look inside `{}` and replace it with the variable's value. So if `text = "play thriller"`, this produces: `did you say "play thriller" boss?`

---

### try/finally — Always Reset is_playing
**Problem (analogy):** A chef only takes one order at a time (`is_playing = True`). If the waiter crashes before telling the chef the order is done, the chef never takes a new order. The kitchen is stuck.

**Fix:** `try/finally` guarantees the kitchen resets no matter what:

```python
try:
    is_playing = True
    await process_song(update, song_name)
    while queue != []:
        song_name = queue.pop(0)
        await process_song(update, song_name)
finally:
    print("resetting is_playing to False")
    is_playing = False  # always runs, even if an error occurs
```

- `try` → attempt the risky operation
- `finally` → no matter what happens (success or crash), always run this

---

### Upload Timeouts
**Problem:** Telegram has a short default timeout for uploads. Large audio files from the Pi take longer, causing silent failures.

**Fix:** Set explicit timeouts on `reply_audio`:
```python
await update.message.reply_audio(
    open('audio.mp3', 'rb'),
    read_timeout=120,
    write_timeout=120,
    connect_timeout=120
)
```

- `connect_timeout` → time to establish connection to Telegram servers
- `write_timeout` → time allowed to upload the file
- `read_timeout` → time to wait for Telegram's confirmation

**Analogy:** The waiter gives the kitchen 120 seconds to plate the food before giving up, instead of the default 10 seconds.

---

### Pi WiFi Tip
Pi 3B+ has a weak WiFi chip. If Telegram connections are timing out, move the Pi physically closer to your hotspot/router. Signal strength directly affects upload reliability.

---

## Marks Summary
| Mark | Feature |
|------|---------|
| Mk1 | `/play` command → YouTube search → download → send to Telegram |
| Mk2 | Voice message → Whisper transcription → play song |
| Mk3 | Queue system, asyncio.Lock, asyncio.to_thread |
| Mk4 | Raspberry Pi deployment, nohup, systemd auto-start |
| Mk5 | Faster-Whisper, lowercase/punctuation fix, try/finally, timeouts |

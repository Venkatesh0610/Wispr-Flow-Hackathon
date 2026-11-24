import asyncio
import os
import tempfile
from typing import Optional, Tuple
from config.settings import settings

VOICE_BY_LANGUAGE = {
    "English": "en-US-AriaNeural",
    "Hindi": "hi-IN-SwaraNeural",
    "Hinglish": "en-IN-NeerjaNeural",
}

def _clean_text(text: str) -> str:
    return text.replace("#", "").replace("*", "").replace("`", "").replace(">", "").strip()

async def _edge_tts_bytes(text: str, voice: str) -> Optional[bytes]:
    import edge_tts

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        mp3_path = tmp.name
    try:
        communicate = edge_tts.Communicate(text=text, voice=voice)
        await communicate.save(mp3_path)
        if os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 0:
            with open(mp3_path, "rb") as f:
                return f.read()
    finally:
        if os.path.exists(mp3_path):
            os.remove(mp3_path)
    return None

def _pyttsx3_bytes(text: str) -> Optional[bytes]:
    import pyttsx3

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        wav_path = tmp.name
    try:
        engine = pyttsx3.init()
        engine.save_to_file(text, wav_path)
        engine.runAndWait()
        if os.path.exists(wav_path) and os.path.getsize(wav_path) > 0:
            with open(wav_path, "rb") as f:
                return f.read()
    finally:
        if os.path.exists(wav_path):
            os.remove(wav_path)
    return None

def synthesize_speech(text: str, language: str = "English") -> Tuple[Optional[bytes], str]:
    """
    Generates speech audio bytes using open-source edge-tts (default) or local pyttsx3.
    Returns (audio_bytes, mime_type).
    """
    clean = _clean_text(text)
    if not clean:
        return None, ""

    preferred_engine = settings.TTS_ENGINE.lower().strip()
    voice = VOICE_BY_LANGUAGE.get(language, settings.TTS_VOICE)

    if preferred_engine == "edge-tts":
        try:
            loop = asyncio.new_event_loop()
            try:
                data = loop.run_until_complete(_edge_tts_bytes(clean, voice))
            finally:
                loop.close()
            if data:
                return data, "audio/mpeg"
        except Exception:
            pass

    try:
        wav_data = _pyttsx3_bytes(clean)
        if wav_data:
            return wav_data, "audio/wav"
    except Exception:
        pass

    return None, ""

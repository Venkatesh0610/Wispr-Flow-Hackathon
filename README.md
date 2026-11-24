# VoiceLearn AI — Conversational Mock Interviewer

An interactive, voice-first mock interview app where the AI asks a question, you answer with **Wispr Flow** (or typing), and the conversation continues dynamically with follow-up probes, scoring, and optional speech playback via **Edge TTS** (with **pyttsx3** local fallback).

## Quickstart
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

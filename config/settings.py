import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    APP_NAME: str = "VoiceLearn — Mock Interview AI"
    TAGLINE: str = "The interviewer asks, you answer, and the conversation flows naturally."
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///mock_interview.db")
    TTS_ENGINE: str = os.getenv("TTS_ENGINE", "edge-tts")  # "edge-tts" | "pyttsx3"
    TTS_VOICE: str = os.getenv("TTS_VOICE", "en-US-AriaNeural")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = "openai/gpt-oss-120b"

    SUPPORTED_LANGUAGES = ["English", "Hindi", "Hinglish"]
    EXPERIENCE_LEVELS = ["Junior", "Mid-Level", "Senior"]
    SUGGESTED_ROLES = [
        "Software Engineer",
        "AI / ML Engineer",
        "Data Scientist",
        "Product Manager",
    ]

settings = Settings()

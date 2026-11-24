# import urllib.request
# from langchain_ollama import ChatOllama
# from config.settings import settings

# def is_ollama_available() -> bool:
#     try:
#         req = urllib.request.Request(f"{settings.OLLAMA_BASE_URL}/api/tags", method="GET")
#         with urllib.request.urlopen(req, timeout=1.5) as resp:
#             return resp.status == 200
#     except Exception:
#         return False

# def get_llm(temperature: float = 0.4) -> ChatOllama:
#     return ChatOllama(
#         base_url=settings.OLLAMA_BASE_URL,
#         model=settings.OLLAMA_MODEL,
#         temperature=temperature,
#     )


from langchain_groq import ChatGroq
from config.settings import settings
from dotenv import load_dotenv
load_dotenv()


def get_llm(temperature: float = 0.4) -> ChatGroq:
    return ChatGroq(
        model=settings.GROQ_MODEL,
        temperature=temperature,
    )
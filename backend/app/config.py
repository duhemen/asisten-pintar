import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Memuat file .env lokal
load_dotenv()

class Settings:
    APP_NAME = "Asisten Pintar"
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:14b-instruct-q4_K_M")
    OLLAMA_VISION_MODEL = os.getenv("OLLAMA_VISION_MODEL", "hf.co/bartowski/Qwen2-VL-2B-Instruct-GGUF:Q4_K_M")
    
    # Folder storage
    STORAGE_DIR = os.getenv("STORAGE_DIR", "storage")
    TEMP_DIR = os.getenv("TEMP_DIR", "temp")

settings = Settings()

# Memastikan folder penyimpanan otomatis dibuat jika belum ada di laptop
for folder in [settings.STORAGE_DIR, settings.TEMP_DIR]:
    os.makedirs(folder, exist_ok=True)
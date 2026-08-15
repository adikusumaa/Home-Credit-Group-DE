# dags/crewai_agents/config.py
import os

# Environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Pilih provider berdasarkan API key yang tersedia
if GEMINI_API_KEY:
    DEFAULT_MODEL = "gemini/gemini-1.5-flash"
elif OPENAI_API_KEY:
    DEFAULT_MODEL = "openai/gpt-4o-mini"
else:
    DEFAULT_MODEL = "gemini/gemini-1.5-flash"

print(f"[Config] Menggunakan model: {DEFAULT_MODEL}")
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración general
DATA_DIR = "data/pdfs"
VECTORSTORE_DIR = "vectorstore"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Modelo de embeddings (se ejecuta localmente)
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

USE_GROQ = True
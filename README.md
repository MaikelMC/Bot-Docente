# Chatbot Asignatura con IA

Sistema de chat inteligente que responde preguntas sobre una asignatura específica usando PDFs como fuente de conocimiento.

## Instalación

1. Crear entorno virtual:
```bash
python -m venv venv
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows
```
Crear directorios:
```bash
mkdir chatbot-asignatura
cd chatbot-asignatura
mkdir data data/pdfs vectorstore static static/css static/js templates
```
Ojo: Si estos comandos no funcionan puedes crear los directorios manualmente.

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

3. Configurar API Key de Gemini o Groq en `.env`

4. Colocar PDFs en `data/pdfs/`

## Uso

1. Procesar PDFs:
```bash
python process_pdfs.py
```

2. Iniciar servidor:
```bash
python app.py
```

3. Abrir navegador en `http://localhost:5000`

## Tecnologías

- Flask
- Sentence Transformers
- FAISS
- Google Gemini API
- PyPDF2
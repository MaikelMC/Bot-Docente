from flask import Flask, render_template, request, jsonify
import os
import pickle
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from config import VECTORSTORE_DIR, GEMINI_API_KEY, GROQ_API_KEY, EMBEDDING_MODEL, USE_GROQ

app = Flask(__name__)

# Configurar LLM según la opción
if USE_GROQ:
    from groq import Groq
    llm_client = Groq(api_key=GROQ_API_KEY)
    print("✅ Usando Groq API")
else:
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-pro')
    print("✅ Usando Gemini API")

# Variables globales
embedding_model = None
faiss_index = None
chunks = None
system_info = None  # Nueva variable para almacenar info del sistema

def load_models():
    """Carga los modelos y datos necesarios"""
    global embedding_model, faiss_index, chunks, system_info
    
    print("🔄 Cargando modelo de embeddings...")
    embedding_model = SentenceTransformer(EMBEDDING_MODEL)
    
    print("🔄 Cargando vectorstore...")
    index_path = os.path.join(VECTORSTORE_DIR, "index.faiss")
    chunks_path = os.path.join(VECTORSTORE_DIR, "chunks.pkl")
    
    # Verificar que existan los archivos
    if not os.path.exists(index_path):
        raise FileNotFoundError(f"❌ No se encontró {index_path}. Ejecuta primero: python process_pdfs.py")
    
    if not os.path.exists(chunks_path):
        raise FileNotFoundError(f"❌ No se encontró {chunks_path}. Ejecuta primero: python process_pdfs.py")
    
    faiss_index = faiss.read_index(index_path)
    
    with open(chunks_path, 'rb') as f:
        chunks = pickle.load(f)
    
    # Verificar que se cargaron datos
    if faiss_index.ntotal == 0:
        raise ValueError("❌ El índice FAISS está vacío!")
    
    if len(chunks) == 0:
        raise ValueError("❌ No hay chunks cargados!")
    
    print(f"✅ Sistema listo:")
    print(f"   - Vectores FAISS: {faiss_index.ntotal}")
    print(f"   - Chunks de texto: {len(chunks)}")
    
    # Generar resumen del sistema
    system_info = generate_system_summary()

def generate_system_summary():
    """Genera un resumen de la información disponible"""
    sources = {}
    for chunk in chunks:
        source = chunk['source']
        if source not in sources:
            sources[source] = []
        sources[source].append(chunk['text'])
    
    # Crear resumen
    summary = {
        'total_chunks': len(chunks),
        'total_documents': len(sources),
        'documents': []
    }
    
    for source, texts in sources.items():
        # Tomar los primeros caracteres de varios chunks para hacer un preview
        preview_text = " ".join(texts[:3])[:500]
        summary['documents'].append({
            'name': source,
            'chunks': len(texts),
            'preview': preview_text
        })
    
    return summary

def search_similar_chunks(query, k=5):  # Aumentado a 5 para mejor contexto
    """Busca los chunks más similares a la pregunta"""
    try:
        # Generar embedding de la pregunta
        query_embedding = embedding_model.encode([query])
        
        # Convertir a formato numpy float32
        query_vector = np.array(query_embedding).astype('float32')
        
        # Buscar en FAISS
        distances, indices = faiss_index.search(query_vector, k)
        
        # Obtener chunks relevantes
        relevant_chunks = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx < len(chunks) and idx >= 0:
                chunk_with_score = chunks[idx].copy()
                chunk_with_score['similarity_score'] = float(distance)
                relevant_chunks.append(chunk_with_score)
        
        # Debug: mostrar scores
        print(f"   Similarity scores: {[f'{c['similarity_score']:.2f}' for c in relevant_chunks]}")
        
        return relevant_chunks
    
    except Exception as e:
        print(f"❌ Error en búsqueda: {e}")
        raise

def generate_answer(question, context_chunks):
    """Genera respuesta usando LLM (Groq o Gemini)"""
    try:
        # Construir contexto
        context = "\n\n".join([
            f"[Fragmento {i+1} de {chunk['source']}]:\n{chunk['text']}" 
            for i, chunk in enumerate(context_chunks)
        ])
        
        # Crear prompt mejorado
        prompt = f"""Eres un asistente educativo experto. Responde la siguiente pregunta basándote ÚNICAMENTE en el contexto proporcionado.

CONTEXTO DISPONIBLE:
{context}

PREGUNTA DEL ESTUDIANTE: {question}

INSTRUCCIONES:
- Responde de forma clara y detallada en español
- Usa TODA la información relevante del contexto proporcionado
- Si encuentras información relacionada en el contexto, úsala aunque no sea una respuesta completa
- Solo di que no tienes información si REALMENTE no hay NADA relacionado en el contexto
- Cita las fuentes mencionando el nombre del documento
- Sé educativo y explica con detalle

RESPUESTA:"""
        
        if USE_GROQ:
            # Usar Groq con modelo correcto
            chat_completion = llm_client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model="moonshotai/kimi-k2-instruct-0905",  # CORREGIDO: Modelo válido de Groq
                temperature=0.5,  # Aumentado para respuestas más naturales
                max_tokens=1500,  # Aumentado para respuestas más completas
            )
            return chat_completion.choices[0].message.content
        else:
            # Usar Gemini
            response = gemini_model.generate_content(prompt)
            return response.text
    
    except Exception as e:
        print(f"❌ Error generando respuesta: {e}")
        return f"Error al generar respuesta: {str(e)}"

@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')

@app.route('/system-info')
def get_system_info():
    """Endpoint para obtener información del sistema"""
    if system_info is None:
        return jsonify({'error': 'Sistema no inicializado'}), 500
    
    return jsonify(system_info)

@app.route('/chat', methods=['POST'])
def chat():
    """Endpoint para procesar preguntas"""
    try:
        data = request.json
        question = data.get('question', '')
        
        if not question:
            return jsonify({'error': 'No se proporcionó pregunta'}), 400
        
        print(f"\n💬 Pregunta recibida: {question}")
        
        # 1. Buscar chunks relevantes
        print("🔍 Buscando información relevante...")
        relevant_chunks = search_similar_chunks(question, k=5)
        print(f"✓ Encontrados {len(relevant_chunks)} fragmentos relevantes")
        
        # 2. Generar respuesta
        print("🤖 Generando respuesta...")
        answer = generate_answer(question, relevant_chunks)
        print("✓ Respuesta generada")
        
        # 3. Preparar fuentes
        sources = list(set([chunk['source'] for chunk in relevant_chunks]))
        
        return jsonify({
            'answer': answer,
            'sources': sources,
            'debug': {
                'chunks_found': len(relevant_chunks),
                'similarity_scores': [chunk['similarity_score'] for chunk in relevant_chunks]
            }
        })
    
    except Exception as e:
        print(f"❌ Error en /chat: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Cargar modelos al iniciar
    try:
        load_models()
    except Exception as e:
        print(f"\n❌ ERROR AL CARGAR SISTEMA: {e}")
        print("\n⚠️  Asegúrate de haber ejecutado: python process_pdfs.py")
        print("⚠️  Y de tener PDFs en la carpeta data/pdfs/\n")
        exit(1)
    
    # Iniciar servidor
    print("\n" + "="*50)
    print("🚀 Servidor iniciado en http://localhost:5000")
    print("="*50 + "\n")
    
    app.run(debug=True, port=5000, use_reloader=False)
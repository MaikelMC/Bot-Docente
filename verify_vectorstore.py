import os
import pickle
import faiss
from config import VECTORSTORE_DIR

def verify_vectorstore():
    """Verifica que el vectorstore esté correctamente creado"""
    
    print("\n" + "="*60)
    print("🔍 VERIFICANDO VECTORSTORE")
    print("="*60)
    
    # Verificar directorio
    if not os.path.exists(VECTORSTORE_DIR):
        print(f"❌ ERROR: No existe el directorio {VECTORSTORE_DIR}")
        return False
    
    print(f"✅ Directorio existe: {VECTORSTORE_DIR}")
    
    # Verificar archivos
    index_path = os.path.join(VECTORSTORE_DIR, "index.faiss")
    chunks_path = os.path.join(VECTORSTORE_DIR, "chunks.pkl")
    
    if not os.path.exists(index_path):
        print(f"❌ ERROR: No existe {index_path}")
        print("   → Ejecuta primero: python process_pdfs.py")
        return False
    
    if not os.path.exists(chunks_path):
        print(f"❌ ERROR: No existe {chunks_path}")
        print("   → Ejecuta primero: python process_pdfs.py")
        return False
    
    print(f"✅ Archivo FAISS existe: {index_path}")
    print(f"✅ Archivo chunks existe: {chunks_path}")
    
    # Cargar y verificar índice FAISS
    try:
        faiss_index = faiss.read_index(index_path)
        print(f"\n📊 Índice FAISS:")
        print(f"   - Vectores almacenados: {faiss_index.ntotal}")
        print(f"   - Dimensión: {faiss_index.d}")
        
        if faiss_index.ntotal == 0:
            print("❌ ERROR: El índice FAISS está vacío!")
            return False
    except Exception as e:
        print(f"❌ ERROR al cargar índice FAISS: {e}")
        return False
    
    # Cargar y verificar chunks
    try:
        with open(chunks_path, 'rb') as f:
            chunks = pickle.load(f)
        
        print(f"\n📄 Chunks de texto:")
        print(f"   - Total de chunks: {len(chunks)}")
        
        if len(chunks) == 0:
            print("❌ ERROR: No hay chunks cargados!")
            return False
        
        # Mostrar fuentes únicas
        sources = set([chunk['source'] for chunk in chunks])
        print(f"   - Documentos procesados: {len(sources)}")
        print(f"\n📚 Fuentes encontradas:")
        for source in sorted(sources):
            count = sum(1 for c in chunks if c['source'] == source)
            print(f"      • {source}: {count} chunks")
        
        # Mostrar ejemplos
        print(f"\n📝 Ejemplos de chunks (primeros 3):")
        for i, chunk in enumerate(chunks[:3]):
            preview = chunk['text'][:150].replace('\n', ' ')
            print(f"\n   Chunk {i+1} [{chunk['source']}]:")
            print(f"   {preview}...")
        
    except Exception as e:
        print(f"❌ ERROR al cargar chunks: {e}")
        return False
    
    print("\n" + "="*60)
    print("✅ VECTORSTORE VERIFICADO CORRECTAMENTE")
    print("="*60 + "\n")
    
    return True

if __name__ == "__main__":
    verify_vectorstore()
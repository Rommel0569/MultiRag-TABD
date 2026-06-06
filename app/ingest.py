# app/ingest.py
import os
import uuid
import json
import numpy as np
import faiss
import easyocr
import cv2
from pdf2image import convert_from_path
from sentence_transformers import SentenceTransformer
import faiss
# -----------------------------
# CONFIGURACIÓN
# -----------------------------
PDF_DIR    = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "..", "data", "pdfs")
INDEX_DIR  = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "..", "data", "index")
POPPLER_PATH = r"C:\Users\USER\Downloads\Release-26.02.0-0\poppler-26.02.0\Library\bin"

os.makedirs(INDEX_DIR, exist_ok=True)

CATEGORIES = {
    "CRONOGRAMA": ["CRONOGRAMA DE ADMISIÓN 2027.pdf"],
    "VACANTES":   ["CUADRO DE VACANTES 2027.pdf"],
    "TEMARIO":    ["TEMARIO Y MATRIZ DE EVALUACIÓN 2027.pdf"],
    "REGLAMENTO": ["REGLAMENTO DE ADMISIÓN 2027.pdf"]
}

# -----------------------------
# MODELOS (se cargan una sola vez)
# -----------------------------
print("[INFO] Cargando EasyOCR (español + inglés)...")
ocr_reader = easyocr.Reader(['es', 'en'], gpu=False)
print("[INFO] EasyOCR listo.")

print("[INFO] Cargando modelo de embeddings...")
embed_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
EMBED_DIM   = embed_model.get_sentence_embedding_dimension()
print(f"[INFO] Embeddings listos. Dimensión: {EMBED_DIM}")

# -----------------------------
# PREPROCESAMIENTO DE IMAGEN
# (técnica del video con OpenCV)
# -----------------------------
def preprocess_image(pil_image):
    """
    Mejora la calidad de la imagen para OCR usando OpenCV.
    Convierte PIL → numpy → escala de grises → blur → threshold adaptativo.
    """
    image = np.array(pil_image)

    # Convertir a escala de grises
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

    # Suavizado gaussiano para reducir ruido
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    # Threshold adaptativo — mejor para documentos escaneados
    thresh = cv2.adaptiveThreshold(
        blur, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11, 2
    )

    return thresh

# -----------------------------
# OCR CON EASYOCR
# -----------------------------
def ocr_pdf(pdf_path):
    """
    Extrae texto de PDF escaneado usando EasyOCR con
    preprocesamiento OpenCV por página.
    """
    print(f"  [PDF] Convirtiendo páginas a imágenes (DPI=300)...")
    pages = convert_from_path(pdf_path, dpi=300, poppler_path=POPPLER_PATH)
    texts = []

    for i, page in enumerate(pages):
        # Preprocesar con OpenCV
        processed = preprocess_image(page)

        # EasyOCR sobre imagen preprocesada
        results   = ocr_reader.readtext(
            processed,
            detail=0,        # solo texto, sin coordenadas
            paragraph=True   # agrupar líneas en párrafos
        )
        page_text = "\n".join(results)
        texts.append((i + 1, page_text))
        print(f"  [OCR] Página {i+1}/{len(pages)} — {len(page_text)} chars extraídos")

    return texts

# -----------------------------
# CHUNKING
# -----------------------------
def chunk_text(text, chunk_size=512, overlap=50):
    """Divide texto en chunks de palabras con solapamiento."""
    words  = text.split()
    chunks = []
    start  = 0
    while start < len(words):
        end   = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        if len(chunk.strip()) > 20:
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks

# -----------------------------
# INGESTA PRINCIPAL
# -----------------------------
def ingest():
    """
    Procesa PDFs → OCR → embeddings → índice FAISS + JSON de metadatos.
    Genera en data/index/:
      <CATEGORIA>.index  — índice FAISS HNSW
      <CATEGORIA>.json   — textos y metadatos
    """
    for category, pdf_list in CATEGORIES.items():
        print(f"\n{'='*55}")
        print(f"[INFO] Categoría: {category}")

        all_texts   = []
        all_vectors = []

        for pdf_file in pdf_list:
            pdf_path = os.path.join(PDF_DIR, pdf_file)
            if not os.path.exists(pdf_path):
                print(f"[WARN] No encontrado: {pdf_path}")
                continue

            print(f"[INFO] Procesando: {pdf_file}")
            pages_text = ocr_pdf(pdf_path)

            for page_num, page_text in pages_text:
                if not page_text.strip():
                    print(f"  [SKIP] Página {page_num} vacía")
                    continue

                chunks = chunk_text(page_text)
                print(f"  [CHUNK] Página {page_num} → {len(chunks)} chunks")

                for chunk in chunks:
                    vector = embed_model.encode(
                        chunk,
                        normalize_embeddings=True
                    )
                    all_vectors.append(vector)
                    all_texts.append({
                        "id":       str(uuid.uuid4()),
                        "text":     chunk,
                        "source":   pdf_file,
                        "page":     page_num,
                        "category": category
                    })

        if not all_vectors:
            print(f"[WARN] Sin vectores para {category}")
            continue

        # -----------------------------
        # CONSTRUIR ÍNDICE FAISS HNSW
        # -----------------------------
        vectors_np = np.array(all_vectors, dtype=np.float32)

        index = faiss.IndexHNSWFlat(EMBED_DIM, 32)
        index.hnsw.efConstruction = 200
        index.hnsw.efSearch        = 50
        index.add(vectors_np)

        # Guardar índice FAISS
        index_path = os.path.join(INDEX_DIR, f"{category}.index")
        faiss.write_index(index, index_path)

        # Guardar textos y metadatos
        json_path = os.path.join(INDEX_DIR, f"{category}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(all_texts, f, ensure_ascii=False, indent=2)

        print(f"\n[OK] {category}:")
        print(f"     Vectores indexados : {index.ntotal}")
        print(f"     Chunks guardados   : {len(all_texts)}")
        print(f"     Índice FAISS       : {index_path}")
        print(f"     Metadatos JSON     : {json_path}")

    print(f"\n{'='*55}")
    print("[DONE] Ingesta completa.")

if __name__ == "__main__":
    ingest()
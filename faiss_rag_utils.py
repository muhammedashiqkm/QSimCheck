import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# Efficient transformer model for fast embedding
model = SentenceTransformer("all-MiniLM-L6-v2")

def embed_texts(texts):
    """Convert list of texts to vector embeddings."""
    return model.encode(texts, convert_to_numpy=True)

def build_faiss_index(questions):
    """Builds a FAISS index from question embeddings."""
    embeddings = embed_texts(questions)
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)
    return index, questions, embeddings

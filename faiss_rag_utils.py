import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# Load open-source embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

def embed_texts(texts):
    return model.encode(texts, convert_to_numpy=True)

def build_faiss_index(questions):
    embeddings = embed_texts(questions)
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)
    return index, questions, embeddings

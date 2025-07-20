import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

model = SentenceTransformer("all-MiniLM-L6-v2")

def embed_texts(texts):
    return model.encode(texts, convert_to_numpy=True)

class SimpleVectorIndex:
    def __init__(self, embeddings):
        self.embeddings = embeddings
    
    def search(self, query_embedding, k=5):
        similarities = cosine_similarity(query_embedding, self.embeddings)
        top_indices = np.argsort(-similarities[0])[:k]
        top_scores = similarities[0][top_indices]
        return np.array([top_scores]), np.array([top_indices])

def build_vector_index(questions):
    embeddings = embed_texts(questions)
    index = SimpleVectorIndex(embeddings)
    return index, questions, embeddings
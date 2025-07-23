import numpy as np
import google.generativeai as genai

def embed_texts(texts):
    """
    Embeds a list of texts using the Google Generative AI embedding model.

    Args:
        texts: A list of strings to be embedded.

    Returns:
        A numpy array of embeddings.
    """
    try:
        # Use the "embedding-001" model for generating embeddings
        result = genai.embed_content(
            model="models/embedding-001",
            content=texts,
            task_type="RETRIEVAL_DOCUMENT"  # Optimized for document search
        )
        return np.array(result['embedding'])
    except Exception as e:
        # Log the exception or handle it as needed
        print(f"An error occurred during embedding: {e}")
        return np.array([])

class SimpleVectorIndex:
    def __init__(self, embeddings):
        """
        Initializes the vector index and pre-normalizes embeddings for efficient search.
        """
        # Calculate the L2 norm for each embedding vector.
        # Add a small epsilon to avoid division by zero.
        norm = np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-8
        # Normalize the embeddings by dividing by their norm.
        self.normalized_embeddings = embeddings / norm
    
    def search(self, query_embedding, k=5):
        """
        Searches for the k-nearest neighbors to the query_embedding.
        """
        # Normalize the single query embedding.
        norm_query = np.linalg.norm(query_embedding) + 1e-8
        normalized_query = query_embedding / norm_query

        # Compute cosine similarity via dot product between the normalized query 
        # and all normalized document embeddings.
        similarities = np.dot(normalized_query, self.normalized_embeddings.T)

        # Get the indices of the top k most similar items.
        # np.argsort sorts in ascending order, so we negate the similarities array
        # to sort in descending order.
        top_indices = np.argsort(-similarities[0])[:k]
        
        # Get the similarity scores for the top indices.
        top_scores = similarities[0][top_indices]
        
        # Return the scores and indices as numpy arrays.
        return np.array([top_scores]), np.array([top_indices])

def build_vector_index(questions):
    """
    Builds a vector index from a list of questions.
    """
    embeddings = embed_texts(questions)
    # Return early if embeddings could not be generated.
    if embeddings.size == 0:
        return None, questions, None
        
    index = SimpleVectorIndex(embeddings)
    return index, questions, embeddings
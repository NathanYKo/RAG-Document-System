from sentence_transformers import SentenceTransformer
import logging

# Initialize logger
logger = logging.getLogger(__name__)

# Load model once at module level for efficiency
model = SentenceTransformer('all-MiniLM-L6-v2')

def generate_embeddings(texts):
    """
    Generate embeddings for a list of texts or a single text
    
    Args:
        texts: String or list of strings to embed
    
    Returns:
        numpy array of embeddings
    """
    try:
        if isinstance(texts, str):
            texts = [texts]
        
        logger.info(f"Generating embeddings for {len(texts)} texts")
        embeddings = model.encode(texts)
        return embeddings
    except Exception as e:
        logger.error(f"Error generating embeddings: {str(e)}")
        raise 
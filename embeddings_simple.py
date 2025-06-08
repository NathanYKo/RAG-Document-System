import numpy as np
import logging
import hashlib
from typing import List, Union

# Initialize logger
logger = logging.getLogger(__name__)

def generate_embeddings(texts: Union[str, List[str]]) -> np.ndarray:
    """
    Generate simple embeddings for texts (for testing purposes)
    This is a basic implementation that creates consistent embeddings
    based on text hashing and basic features.
    
    Args:
        texts: String or list of strings to embed
    
    Returns:
        numpy array of embeddings
    """
    try:
        if isinstance(texts, str):
            texts = [texts]
        
        logger.info(f"Generating simple embeddings for {len(texts)} texts")
        
        embeddings = []
        for text in texts:
            # Create a basic embedding based on text characteristics
            # This is for testing only - in production use sentence-transformers
            
            # Hash-based features
            text_hash = hashlib.md5(text.encode()).hexdigest()
            hash_features = [int(text_hash[i:i+2], 16) / 255.0 for i in range(0, 32, 2)]
            
            # Text length features
            length_features = [
                min(len(text) / 1000.0, 1.0),  # normalized length
                len(text.split()) / 100.0,     # word count
                text.count(' ') / max(len(text), 1),  # space ratio
            ]
            
            # Character frequency features (basic)
            char_features = [
                text.lower().count(char) / max(len(text), 1) 
                for char in 'aeiou'
            ]
            
            # Combine all features to create a 384-dimensional embedding
            # (similar to sentence-transformers output size)
            embedding = hash_features + length_features + char_features
            
            # Pad or truncate to 384 dimensions
            while len(embedding) < 384:
                embedding.append(0.0)
            embedding = embedding[:384]
            
            embeddings.append(embedding)
        
        return np.array(embeddings, dtype=np.float32)
        
    except Exception as e:
        logger.error(f"Error generating embeddings: {str(e)}")
        raise 
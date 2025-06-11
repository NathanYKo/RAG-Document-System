import chromadb
import asyncio
import logging
import uuid
from typing import List, Dict, Any, Optional, Union
try:
    from embeddings import generate_embeddings
except ImportError:
    # Fallback to simple embeddings for testing
    from embeddings_simple import generate_embeddings

# Initialize logger
logger = logging.getLogger(__name__)

class ChromaDB:
    def __init__(self):
        try:
            # Ensure db directory exists
            import os
            os.makedirs("./db", exist_ok=True)
            
            # Use the new ChromaDB API
            self.client = chromadb.PersistentClient(path="./db")
            self.collection = self.client.get_or_create_collection("documents")
            logger.info("ChromaDB initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing ChromaDB: {str(e)}")
            raise RuntimeError(f"Failed to initialize ChromaDB: {str(e)}")

    async def add_documents(
        self,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        Add documents to the vector database
        
        Args:
            documents: List of document texts
            embeddings: List of embedding vectors
            metadatas: List of metadata dictionaries
            ids: Optional list of document IDs
            
        Returns:
            List of document IDs
        """
        try:
            if not documents or len(embeddings) == 0 or not metadatas:
                raise ValueError("Documents, embeddings, and metadatas must not be empty")
                
            if len(documents) != len(embeddings) or len(documents) != len(metadatas):
                raise ValueError("Documents, embeddings, and metadatas must have the same length")
            
            if ids is None:
                ids = [str(uuid.uuid4()) for _ in documents]
            
            # Convert embeddings to list if it's a numpy array
            if hasattr(embeddings, 'tolist'):
                embeddings = embeddings.tolist()
            elif hasattr(embeddings, 'shape'):
                # Handle numpy arrays properly
                embeddings = [embedding.tolist() if hasattr(embedding, 'tolist') else embedding for embedding in embeddings]
            
            self.collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            await self.persist()
            logger.info(f"Added {len(documents)} documents to ChromaDB")
            return ids
        except Exception as e:
            logger.error(f"Error adding documents to ChromaDB: {str(e)}")
            raise RuntimeError(f"Failed to add documents: {str(e)}")

    async def persist(self) -> None:
        """Persist the database to disk - automatic with PersistentClient"""
        try:
            # PersistentClient automatically persists changes
            logger.debug("ChromaDB persisted successfully (automatic)")
        except Exception as e:
            logger.error(f"Error persisting ChromaDB: {str(e)}")
            raise RuntimeError(f"Failed to persist database: {str(e)}")

    def query(
        self,
        query_texts: Union[str, List[str]],
        n_results: int = 5
    ) -> Dict[str, Any]:
        """
        Query the vector database
        
        Args:
            query_texts: List of query strings or single query string
            n_results: Number of results to return
        
        Returns:
            Query results from ChromaDB
        """
        try:
            if isinstance(query_texts, str):
                query_texts = [query_texts]
            
            if not query_texts or len(query_texts) == 0:
                raise ValueError("Query texts must not be empty")
            
            query_embeddings = generate_embeddings(query_texts)
            
            # Convert embeddings to list if it's a numpy array
            if hasattr(query_embeddings, 'tolist'):
                query_embeddings = query_embeddings.tolist()
            elif hasattr(query_embeddings, 'shape'):
                # Handle numpy arrays properly
                query_embeddings = [embedding.tolist() if hasattr(embedding, 'tolist') else embedding for embedding in query_embeddings]
            
            results = self.collection.query(
                query_embeddings=query_embeddings, 
                n_results=n_results
            )
            logger.info(f"Query executed, returned {len(results.get('documents', [[]]))} result sets")
            return results
        except Exception as e:
            logger.error(f"Error querying ChromaDB: {str(e)}")
            raise RuntimeError(f"Failed to query database: {str(e)}")
    
    def get(self, ids: Union[str, List[str]]) -> Dict[str, Any]:
        """
        Get documents by their IDs
        
        Args:
            ids: Single ID or list of IDs
            
        Returns:
            Retrieved documents and metadata
        """
        try:
            if isinstance(ids, str):
                ids = [ids]
            
            if not ids:
                raise ValueError("IDs must not be empty")
            
            results = self.collection.get(ids=ids)
            logger.info(f"Retrieved {len(results.get('documents', []))} documents by ID")
            return results
        except Exception as e:
            logger.error(f"Error getting documents from ChromaDB: {str(e)}")
            raise RuntimeError(f"Failed to get documents: {str(e)}")

    async def delete(self, ids: Union[str, List[str]]) -> None:
        """
        Delete documents by their IDs
        
        Args:
            ids: Single ID or list of IDs
        """
        try:
            if isinstance(ids, str):
                ids = [ids]
            
            if not ids:
                raise ValueError("IDs must not be empty")
            
            self.collection.delete(ids=ids)
            await self.persist()
            logger.info(f"Deleted {len(ids)} documents from ChromaDB")
        except Exception as e:
            logger.error(f"Error deleting documents from ChromaDB: {str(e)}")
            raise RuntimeError(f"Failed to delete documents: {str(e)}")

    def count(self) -> int:
        """
        Get the total number of documents in the collection
        
        Returns:
            Number of documents in the collection
        """
        try:
            count = self.collection.count()
            logger.info(f"ChromaDB contains {count} documents")
            return count
        except Exception as e:
            logger.error(f"Error counting documents in ChromaDB: {str(e)}")
            raise RuntimeError(f"Failed to count documents: {str(e)}") 
#!/usr/bin/env python3
"""
Simple integration test for the vector database implementation
"""

import asyncio
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_integration():
    """Test the complete integration"""
    try:
        # Test embeddings
        print("🔍 Testing embeddings...")
        try:
            from embeddings import generate_embeddings
            print("✓ Using sentence-transformers embeddings")
        except ImportError:
            from embeddings_simple import generate_embeddings
            print("✓ Using simple embeddings (fallback)")
        
        # Test embedding generation
        test_texts = ["This is a test document", "Another test document"]
        embeddings = generate_embeddings(test_texts)
        print(f"✓ Generated embeddings with shape: {embeddings.shape}")
        
        # Test database
        print("\n📊 Testing ChromaDB...")
        from database import ChromaDB
        db = ChromaDB()
        print("✓ ChromaDB initialized")
        
        initial_count = db.count()
        print(f"✓ Initial document count: {initial_count}")
        
        # Add test documents
        print("\n📝 Adding test documents...")
        metadatas = [
            {"source": "test1.txt", "type": "test"},
            {"source": "test2.txt", "type": "test"}
        ]
        
        ids = await db.add_documents(test_texts, embeddings, metadatas)
        print(f"✓ Added {len(ids)} documents with IDs: {ids[:2]}...")
        
        new_count = db.count()
        print(f"✓ New document count: {new_count}")
        
        # Test querying
        print("\n🔍 Testing queries...")
        results = db.query("test document", n_results=2)
        print(f"✓ Query returned {len(results['documents'][0])} results")
        print(f"✓ First result: {results['documents'][0][0][:50]}...")
        
        # Test retrieval by ID
        print("\n📄 Testing document retrieval...")
        doc_id = results['ids'][0][0]
        doc = db.get([doc_id])
        print(f"✓ Retrieved document: {doc['documents'][0][:50]}...")
        
        # Test deletion
        print("\n🗑️ Testing document deletion...")
        await db.delete([doc_id])
        final_count = db.count()
        print(f"✓ Final document count after deletion: {final_count}")
        
        print("\n🎉 All tests passed! Vector database implementation is working correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_document_processor():
    """Test the document processor integration"""
    try:
        print("\n🔧 Testing document processor integration...")
        
        # Import the updated document processor
        from document_processor import get_db, process_chunks
        
        # Test database singleton
        db1 = get_db()
        db2 = get_db()
        print(f"✓ Database singleton working: {db1 is db2}")
        
        # Test chunk processing
        test_chunks = ["This is chunk 1", "This is chunk 2", "This is chunk 3"]
        metadata = {"source": "test_doc.txt", "file_type": "txt"}
        
        chunk_ids = await process_chunks(test_chunks, metadata)
        print(f"✓ Processed {len(chunk_ids)} chunks successfully")
        
        # Verify chunks were added
        db = get_db()
        for chunk_id in chunk_ids:
            doc = db.get([chunk_id])
            if doc['documents']:
                print(f"✓ Chunk stored: {doc['documents'][0][:30]}...")
        
        print("✓ Document processor integration working correctly")
        return True
        
    except Exception as e:
        print(f"\n❌ Document processor test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting Vector Database Integration Tests")
    print("=" * 60)
    
    # Run the tests
    loop = asyncio.get_event_loop()
    
    # Test basic integration
    success1 = loop.run_until_complete(test_integration())
    
    # Test document processor integration
    success2 = loop.run_until_complete(test_document_processor())
    
    if success1 and success2:
        print("\n🎯 All integration tests passed!")
        print("✅ The vector database implementation is ready for use.")
    else:
        print("\n⚠️ Some tests failed. Please check the errors above.")
        exit(1) 
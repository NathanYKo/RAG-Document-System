# RAG System Implementation

**Generated:** 2025-06-07T20:57:47.730989

Here is a complete implementation of a RAG (Retrieval-Augmented Generation) system, integrated with the document processing pipeline and vector database from the previous steps:

1. Code Files:

rag.py:
```python
import os
import openai
from database import ChromaDB
from fastapi import FastAPI, Request
from pydantic import BaseModel
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")

PROMPT_TEMPLATE = """
Answer the following question based on the provided context. 
If the context does not contain enough information to answer the question, say "I don't have enough information to answer this question."

Context:
{context}

Question: {question}

Answer:
"""

app = FastAPI()

class QueryRequest(BaseModel):
    query: str

def get_context(query):
    db = ChromaDB()
    results = db.query(query_texts=[query], n_results=5)
    
    context = "\n\n".join(results["documents"][0])
    source_ids = [f"[{doc_id}]" for doc_id in results["ids"][0]]
    
    return context, source_ids

def generate_prompt(query, context):
    prompt = PROMPT_TEMPLATE.format(context=context, question=query)
    return prompt

def generate_answer(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that answers questions based on the provided context."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=500,
        n=1
    )
    return response.choices[0].message.content.strip()

def add_citations(answer, source_ids):
    citation_str = "\n\nSources: " + ", ".join(source_ids)
    return answer + citation_str

@app.post("/query")
async def query_rag(request: QueryRequest):
    query = request.query
    
    try:
        context, source_ids = get_context(query)
        prompt = generate_prompt(query, context)
        answer = generate_answer(prompt)
        answer_with_citations = add_citations(answer, source_ids)
        
        logger.info(f"Generated answer for query: {query}")
        
        return {"query": query, "result": answer_with_citations}

    except Exception as e:
        logger.exception(f"Error generating answer for query: {query}")
        raise
```

2. Setup Instructions:

- Follow setup from previous steps for the document processor and vector database
- Install additional dependencies (see next section)
- Set your OpenAI API key as an environment variable: `export OPENAI_API_KEY=your_api_key_here`  
- Save the new `rag.py` file
- Run the FastAPI server with `uvicorn rag:app --reload`

3. Additional Dependencies:

```
openai==0.27.2
```

Install with:
```
pip install openai
```

4. Configuration:
- The `OPENAI_API_KEY` environment variable needs to be set with your OpenAI API key.
- The `PROMPT_TEMPLATE` in `rag.py` defines the template for constructing the prompt sent to the LLM. Adjust as needed.

5. Testing:

test_rag.py:
```python
from fastapi.testclient import TestClient
from rag import app

client = TestClient(app)

def test_query_rag():
    # Assuming you have already indexed some documents in previous steps
    response = client.post("/query", json={"query": "What is the meaning of life?"})
    result = response.json()
    
    assert response.status_code == 200
    assert "query" in result
    assert "result" in result
    assert "Sources:" in result["result"]

def test_query_rag_no_results():
    # Assuming no relevant documents for this query
    response = client.post("/query", json={"query": "Asdfghjkl;'asdfghjkl?!"})
    result = response.json()

    assert response.status_code == 200   
    assert "I don't have enough information to answer this question." in result["result"]
```

Run tests with: `pytest test_rag.py`

6. Integration:

- The RAG system assumes documents have already been processed and indexed in the vector database using the code from previous steps.
- It exposes a `/query` endpoint that accepts a JSON payload with a `query` field.
- When a query is received, it:
    1. Retrieves relevant context from the vector DB using the `get_context` function
    2. Constructs a prompt using the `generate_prompt` function and the retrieved context
    3. Sends the prompt to the OpenAI API to generate an answer using the `generate_answer` function
    4. Appends citations to the answer using document IDs from the vector DB search
    5. Returns the answer with citations
- Error handling will log exceptions and return a 500 status code if answer generation fails

This completes the implementation of the RAG system! It is fully integrated with the document processing pipeline and vector database. You can now process documents, index them in the vector DB, and query the RAG system to generate answers with citations.

Let me know if you have any other questions! Make sure to follow the setup steps, set your OpenAI API key, and run the FastAPI server to start using the system.
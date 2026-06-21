# rag/retriever.py
"""
Retriever module for the VillageTaste Resort RAG pipeline.
Loads the persisted vector store and implements the interface to query resort knowledge offline.
"""

import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:
    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings
    except ImportError:
        HuggingFaceEmbeddings = None

try:
    from langchain_chroma import Chroma
except ImportError:
    try:
        from langchain_community.vectorstores import Chroma
    except ImportError:
        Chroma = None

# Global variables for caching the model and vector database connection in-memory
_embeddings_cache = None
_vector_store_cache = None


def get_embeddings():
    """
    Helper to instantiate and cache HuggingFace BGE Embeddings locally.
    """
    global _embeddings_cache
    if HuggingFaceEmbeddings is None:
        raise ImportError(
            "HuggingFaceEmbeddings could not be imported. Please verify that "
            "either 'langchain-huggingface' or 'langchain-community' is installed."
        )
    
    if _embeddings_cache is None:
        model_name = "BAAI/bge-base-en-v1.5"
        model_kwargs = {"device": "cpu"}
        encode_kwargs = {"normalize_embeddings": True}
        
        _embeddings_cache = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs=model_kwargs,
            encode_kwargs=encode_kwargs
        )
    return _embeddings_cache


def get_vector_store():
    """
    Helper to load and cache the persisted ChromaDB database.
    """
    global _vector_store_cache
    if Chroma is None:
        raise ImportError(
            "Chroma could not be imported. Please verify that "
            "either 'langchain-chroma' or 'langchain-community' is installed."
        )
        
    if _vector_store_cache is None:
        vector_store_path = PROJECT_ROOT / "vector_store"
        
        if not vector_store_path.exists():
            raise FileNotFoundError(
                f"Vector store directory '{vector_store_path.resolve()}' not found. "
                "You must run ingestion first to generate the database. "
                "Command: python rag/ingest.py"
            )
            
        _vector_store_cache = Chroma(
            persist_directory=str(vector_store_path),
            embedding_function=get_embeddings()
        )
    return _vector_store_cache


def search_resort_knowledge(query: str, category: str = None) -> dict:
    """
    Queries the persisted vector database for top 3 matching documents.
    If category is provided, it filters/narrows document retrieval based on source paths.
    
    Parameters:
        query (str): The search phrase or question.
        category (str, optional): The FAQ category to narrow document retrieval.
        
    Returns:
        dict: A dictionary containing:
            - 'query': original question
            - 'results': list of dicts with 'content', 'source', and 'score' (L2 distance)
    """
    if category:
        print(f"[RAG Retriever] Searching knowledge base for query: '{query}' with category filter: '{category}'")
    else:
        print(f"[RAG Retriever] Searching knowledge base for query: '{query}'")
    
    try:
        db = get_vector_store()
        
        # If filtering by category, retrieve more candidates to ensure we find matches after filtering
        k_val = 10 if category else 3
        results = db.similarity_search_with_score(query, k=k_val)
        
        allowed_sources = []
        if category:
            cat_lower = category.lower()
            if "activities" in cat_lower:
                allowed_sources = ["activities/activities.md", "faqs/faqs.md"]
            elif "dining" in cat_lower:
                allowed_sources = ["menu/menu.md", "faqs/faqs.md"]
            elif "accommodation" in cat_lower:
                allowed_sources = ["resort_info/resort_info.md", "faqs/faqs.md"]
            elif "policies" in cat_lower:
                allowed_sources = ["policies/policies.md", "faqs/faqs.md"]
            elif "transportation" in cat_lower:
                allowed_sources = ["faqs/faqs.md"]
                
        formatted_results = []
        for doc, score in results:
            source = doc.metadata.get("source", "unknown")
            if allowed_sources and source not in allowed_sources:
                continue
            formatted_results.append({
                "content": doc.page_content,
                "source": source,
                "score": float(score)  # Convert float32 to standard float for serialization
            })
            
        # Fallback to top 3 unfiltered if filtered results are empty
        if category and not formatted_results:
            formatted_results = []
            for doc, score in results[:3]:
                formatted_results.append({
                    "content": doc.page_content,
                    "source": doc.metadata.get("source", "unknown"),
                    "score": float(score)
                })
        else:
            formatted_results = formatted_results[:3]
            
        return {
            "query": query,
            "category": category,
            "results": formatted_results
        }
        
    except Exception as e:
        print(f"[Error] Failed to query knowledge base: {e}")
        return {
            "query": query,
            "results": [],
            "error": str(e)
        }


# Quick standalone run option for manual testing
if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_query = " ".join(sys.argv[1:])
    else:
        test_query = "What pottery workshops are available?"
        
    print(f"Executing manual test for: '{test_query}'")
    try:
        search_results = search_resort_knowledge(test_query)
        import json
        print(json.dumps(search_results, indent=2))
    except Exception as ex:
        print(f"Execution failed: {ex}")

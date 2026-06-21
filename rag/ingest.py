# rag/ingest.py
"""
Ingestion script for the VillageTaste Resort RAG pipeline.
Recursively crawls knowledge_base/ for .md files, chunks them,
generates local BAAI/bge-base-en-v1.5 embeddings, and saves them to ChromaDB.
"""

import os
import sys
from pathlib import Path

# Add project root to path to ensure modules are discoverable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

# Dependency Validation
REQUIRED_PACKAGES = {
    "langchain": "langchain",
    "langchain_text_splitters": "langchain-text-splitters",
    "langchain_huggingface": "langchain-huggingface",
    "langchain_chroma": "langchain-chroma",
    "sentence_transformers": "sentence-transformers",
    "chromadb": "chromadb"
}

missing_packages = []
for module, package in REQUIRED_PACKAGES.items():
    try:
        __import__(module)
    except ImportError:
        # Check alternative older names for fallback
        if module == "langchain_text_splitters":
            try:
                __import__("langchain.text_splitter")
                continue
            except ImportError:
                pass
        elif module == "langchain_huggingface":
            try:
                __import__("langchain_community.embeddings")
                continue
            except ImportError:
                pass
        elif module == "langchain_chroma":
            try:
                __import__("langchain_community.vectorstores")
                continue
            except ImportError:
                pass
        missing_packages.append(package)

if missing_packages:
    print("=" * 80)
    print("WARNING: Missing required dependencies to run ingestion:")
    for pkg in missing_packages:
        print(f"  - {pkg}")
    print("\nPlease run the following command to install dependencies:")
    print("pip install langchain langchain-text-splitters langchain-huggingface langchain-chroma sentence-transformers chromadb")
    print("=" * 80)
    # We do not call sys.exit(1) here so imports can still be viewed/parsed
    # in editor environments, but we raise it during main script run.


from langchain_core.documents import Document

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    from langchain.text_splitter import RecursiveCharacterTextSplitter

try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:
    from langchain_community.embeddings import HuggingFaceEmbeddings

try:
    from langchain_chroma import Chroma
except ImportError:
    from langchain_community.vectorstores import Chroma


def crawl_and_load_documents(kb_dir: Path) -> list[Document]:
    """
    Recursively finds every .md file in the knowledge base and loads it.
    """
    documents = []
    
    if not kb_dir.exists():
        raise FileNotFoundError(f"Knowledge base directory '{kb_dir}' does not exist.")
        
    for root, _, files in os.walk(kb_dir):
        for file in files:
            if file.endswith('.md'):
                file_path = Path(root) / file
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    # Store file path relative to knowledge_base root for clean source tracing
                    relative_source = file_path.relative_to(kb_dir).as_posix()
                    
                    doc = Document(
                        page_content=content,
                        metadata={
                            "source": relative_source,
                            "file_name": file
                        }
                    )
                    documents.append(doc)
                except Exception as e:
                    print(f"[Error] Failed to load document '{file_path}': {e}")
                    
    return documents


def run_ingestion():
    """
    Main ingestion execution block.
    Loads documents, splits into chunks, initializes BGE embeddings, and saves to database.
    """
    if missing_packages:
        print("[Abort] Missing dependencies. Exiting ingestion.")
        sys.exit(1)

    kb_path = PROJECT_ROOT / "knowledge_base"
    vector_store_path = PROJECT_ROOT / "vector_store"
    
    print("\n--- Starting VillageTaste Knowledge Ingestion ---")
    print(f"Reading documents from: {kb_path.resolve()}")
    
    # 1. Load documents recursively
    documents = crawl_and_load_documents(kb_path)
    print(f"[Ingestion Log] Loaded {len(documents)} source markdown documents.")
    
    if not documents:
        print("[Warning] No markdown documents found in knowledge base. Ingestion stopped.")
        return

    # 2. Chunk documents
    print("[Ingestion Log] Chunking documents (size=500, overlap=50)...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    chunks = splitter.split_documents(documents)
    print(f"[Ingestion Log] Created {len(chunks)} text chunks.")

    # 3. Load HuggingFace BGE Embeddings model (runs entirely locally)
    print("[Ingestion Log] Initializing BAAI/bge-base-en-v1.5 embedding model...")
    print("               (Note: Weights will download automatically on the first execution)")
    model_name = "BAAI/bge-base-en-v1.5"
    model_kwargs = {"device": "cpu"}
    encode_kwargs = {"normalize_embeddings": True}
    
    embeddings = HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs
    )

    # 4. Save to ChromaDB
    print(f"[Ingestion Log] Storing and indexing embeddings in ChromaDB at: {vector_store_path.resolve()}...")
    
    # Clean vector store directory if it already exists to prevent duplicate indexes
    if vector_store_path.exists():
        import shutil
        print("[Ingestion Log] Existing vector store found. Clearing old index...")
        try:
            shutil.rmtree(vector_store_path)
        except Exception as e:
            print(f"[Warning] Failed to clear vector store path: {e}")

    db = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(vector_store_path)
    )
    
    # Persist the store to disk (for backward-compatible versions of LangChain Chroma)
    if hasattr(db, "persist"):
        db.persist()
        
    print("[Ingestion Log] Vector database saved successfully.")
    print("--- Ingestion Complete ---\n")


if __name__ == "__main__":
    run_ingestion()

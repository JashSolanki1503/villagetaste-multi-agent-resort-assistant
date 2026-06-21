# tests/test_rag.py
"""
Unit tests for the local RAG pipeline infrastructure.
Tests document crawling against actual files and verifies the query response format.
Runs offline without requiring third-party vector/embedding packages to be pre-installed.
"""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure the root project directory is in the python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

# --- Local Mocks for Testing without ChromaDB/HuggingFace Installed ---

class MockDocument:
    def __init__(self, page_content, metadata=None):
        self.page_content = page_content
        self.metadata = metadata or {}

class MockChroma:
    @classmethod
    def from_documents(cls, documents, embedding, persist_directory):
        instance = cls()
        instance.documents = documents
        instance.persist_directory = persist_directory
        return instance
        
    def similarity_search_with_score(self, query, k=3):
        # Simulate returning matching documents and Euclidean L2 distance scores
        doc1 = MockDocument("This is a simulated snippet about pottery.", {"source": "activities/activities.md"})
        doc2 = MockDocument("Organic dining includes farm-fresh salad.", {"source": "menu/menu.md"})
        return [(doc1, 0.15), (doc2, 0.38)]

# Inject mock libraries into sys.modules
sys.modules["langchain_core"] = MagicMock()
sys.modules["langchain_core.documents"] = MagicMock()
sys.modules["langchain_core.documents"].Document = MockDocument

sys.modules["langchain_text_splitters"] = MagicMock()
sys.modules["langchain_huggingface"] = MagicMock()
sys.modules["langchain_chroma"] = MagicMock()
sys.modules["langchain_chroma"].Chroma = MockChroma

# Now import the components under test
from rag.ingest import crawl_and_load_documents
from rag.retriever import search_resort_knowledge


class TestRAGPipeline(unittest.TestCase):
    
    def test_crawl_and_load_documents(self):
        """
        Verifies that the document crawler walks the knowledge_base directory,
        correctly identifies all .md files, reads their contents, and stores
        clean, relative paths in the source metadata.
        """
        kb_path = PROJECT_ROOT / "knowledge_base"
        docs = crawl_and_load_documents(kb_path)
        
        # We expect at least 5 documents corresponding to the 5 categories
        self.assertGreaterEqual(len(docs), 5)
        
        # Verify metadata structures
        sources = [doc.metadata["source"] for doc in docs]
        self.assertIn("activities/activities.md", sources)
        self.assertIn("menu/menu.md", sources)
        self.assertIn("resort_info/resort_info.md", sources)
        
        # Ensure path strings are normalized relative to knowledge_base
        first_doc = docs[0]
        self.assertNotIn("d:", first_doc.metadata["source"].lower())
        self.assertNotIn("\\", first_doc.metadata["source"])
        
    @patch("rag.retriever.get_vector_store")
    def test_search_resort_knowledge_format(self, mock_get_store):
        """
        Verifies that search_resort_knowledge retrieves matching chunks and formats
        the response structure accurately with scores, relative source files, and text.
        """
        # Configure the mock store returning the predefined search mock values
        mock_get_store.return_value = MockChroma()
        
        response = search_resort_knowledge("what workshops are there?")
        
        # Verify response wrapper structure
        self.assertEqual(response["query"], "what workshops are there?")
        self.assertIn("results", response)
        self.assertEqual(len(response["results"]), 2)
        
        # Verify items format
        first_item = response["results"][0]
        self.assertEqual(first_item["content"], "This is a simulated snippet about pottery.")
        self.assertEqual(first_item["source"], "activities/activities.md")
        self.assertEqual(first_item["score"], 0.15)
        
        second_item = response["results"][1]
        self.assertEqual(second_item["content"], "Organic dining includes farm-fresh salad.")
        self.assertEqual(second_item["source"], "menu/menu.md")
        self.assertEqual(second_item["score"], 0.38)


if __name__ == "__main__":
    unittest.main()

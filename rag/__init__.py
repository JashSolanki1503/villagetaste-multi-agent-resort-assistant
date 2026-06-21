# rag/__init__.py
"""
VillageTaste Resort RAG (Retrieval-Augmented Generation) Module.
Exposes the query interface to search the resort's local knowledge base offline.
"""

from .retriever import search_resort_knowledge

__all__ = [
    "search_resort_knowledge",
]

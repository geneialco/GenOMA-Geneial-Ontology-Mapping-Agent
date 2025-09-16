"""
Agent registry and execution module for the UMLS Mapping LangGraph-based Agent.
This module builds and exposes the main agent for medical term mapping workflows.
"""

from src.graph.builder import build_umls_mapper_graph

# Build and expose the main UMLS mapping agent
# This agent handles the complete workflow from medical term extraction to ontology mapping
umls_mapper_agent = build_umls_mapper_graph()


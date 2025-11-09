"""
Docling Module - Document Processing Package
=============================================

Main Components:
    - DoclingPDFProcessor: Main processor class
    - DocumentConfig: Configuration data class
    - ProcessingResult: Result data class
    - DocumentProcessorFactory: Factory for creating processors
    - docling_process: Simple function API

Usage:
    from docling_module import docling_process
    
    result = docling_process("document.pdf")
    if result.success:
        print(result.content)
"""

from .processor import (
    # Main classes
    DoclingPDFProcessor,
    DocumentProcessorInterface,
    DocumentProcessorFactory,
    
    # Data classes
    ProcessingResult,
    DocumentConfig,
    
    # Simple function API
    docling_process,
)

__version__ = "1.0.0"
__author__ = "Your Name"

__all__ = [
    # Classes
    "DoclingPDFProcessor",
    "DocumentProcessorInterface",
    "DocumentProcessorFactory",
    "ProcessingResult",
    "DocumentConfig",
    
    # Functions
    "docling_process",
]

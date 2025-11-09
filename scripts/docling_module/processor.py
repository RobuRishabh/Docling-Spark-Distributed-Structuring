## This contains the core Python function (docling processor) that handles the actual document processing.
## It should have zero PySpark imports or spark-specific code.

# standard imports
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod
import json

# Docling imports
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend

@dataclass
class ProcessingResult:
    """
    Encapsulates the result of document processing.
    Attributes:
    - success (bool): Whether the processing was successful.
    - content (str): The processed content of the document.
    - metadata (Dict): Additional metadata about the document.
    - error_message (Optional[str]): Error message if processing failed.
    - file_path (str): Original file path that was processed.
    """
    success: bool
    content: str
    metadata: Dict[str, Any]
    error_message: Optional[str]
    file_path: str

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the ProcessingResult to a dictionary.
        """
        return {
            "success": self.success,
            "content": self.content,
            "metadata": self.metadata,
            "error_message": self.error_message,
            "file_path": self.file_path,
        }

    def __str__(self) -> str:
        """
        Return a string representation of the ProcessingResult.
        """
        status = "SUCCESS" if self.success else "FAILED"
        return f"ProcessingResult(success={status}, file_path={self.file_path})"

@dataclass
class DocumentConfig:
    """
    Configuration for document processing.
    """
    extract_tables: bool = True
    extract_images: bool = True
    ocr_enabled: bool = True
    max_pages: Optional[int] = None
    
class DocumentProcessorInterface(ABC):
    """
    Interface for document processors.
    """
    @abstractmethod
    def process(self, file_path:str) -> ProcessingResult:
        """
        Process a document and return the result.
        """
        pass
    @abstractmethod
    def validate_file(self, file_path:str) -> bool:
        """
        Validate a file before processing.
        """
        pass

class DoclingPDFProcessor(DocumentProcessorInterface):
    """
    Processor for PDF documents.
    """
    def __init__(self, config: Optional[DocumentConfig] = None):
        """
        Initialize the DoclingPDFProcessor.
        """
        self._config = config if config else DocumentConfig()
        # Initialize the docling converter
        self._converter = self._initialize_converter()
        # class level constants (immutable)
        self._supported_extensions = ['.pdf']

    def _initialize_converter(self) -> DocumentConverter:
        """
        Initialize the Docling converter.
        """
        # Create pipeline options based on the configuration
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_table_structure = self._config.extract_tables
        pipeline_options.do_ocr = self._config.ocr_enabled

        # Create and return the converter
        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: pipeline_options
                },
        )
        return converter 

    def validate_file(self, file_path:str) -> bool:
        """
        Validate a file before processing.
        """
        path_obj = Path(file_path)

        # File must exist
        if not path_obj.exists():
            return False

        # Must be a file (not a directory)
        if not path_obj.is_file():
            return False

        # Must have a supported extension
        if path_obj.suffix.lower() not in self._supported_extensions:
            return False
        
        return True

    def process(self, file_path:str) -> ProcessingResult:
        """
        Process a document and return the result.
        """
        try:
            # Validate the file
            if not self.validate_file(file_path):
                return ProcessingResult(
                    success=False,
                    content="",
                    metadata={},
                    error_message="Invalid file",
                    file_path=file_path
                )

            # Convert the document using docling
            result = self._converter.convert(file_path)

            # Extract the content and metadata
            markdown_content = result.document.export_to_markdown()
            metadata = self._extract_metadata(result, file_path)
            
            # Return success result
            return ProcessingResult(
                success=True,
                content=markdown_content,
                metadata=metadata,
                error_message=None,
                file_path=file_path
            )
        except Exception as e:
            # Error handling - return failure result with error message
            return ProcessingResult(
                success=False,
                content="",
                metadata={},
                error_message=f"Error processing {file_path}: {str(e)}",
                file_path=file_path
            )

    def _extract_metadata(self, docling_result, file_path:str) -> Dict[str, Any]:
        """
        Extract metadata from the Docling result.
        """
        path_obj = Path(file_path)
        metadata = {
            "file_name": path_obj.name,
            "file_size": path_obj.stat().st_size,
            "file_extension": path_obj.suffix,
            "file_path": file_path,
            "num_pages": getattr(docling_result.document, 'page_count', 0),
        }
        # Add document-level metadata if available
        if hasattr(docling_result.document, 'metadata'):
            metadata['document_metadata'] = docling_result.document.metadata
        
        return metadata

    def process_directory(self, directory_path:str) -> List[ProcessingResult]:
        """
        Process all PDFs in the directory
        """
        results = []
        dir_path = Path(directory_path)
        if not dir_path.exists() or not dir_path.is_dir():
            raise ValueError(f"Directory {directory_path} does not exist or is not a directory")

        # Iterate through all PDF files
        for pdf_file in dir_path.glob("*.pdf"):
            # OOP Concept: METHOD REUSE - calling process for each file
            result = self.process(str(pdf_file))
            results.append(result)
        
        return results
    
    def get_config(self) -> DocumentConfig:
        """
        Get the configuration for the processor.
        """
        return self._config
    
    def update_config(self, config: DocumentConfig) -> None:
        """
        Update the configuration for the processor.
        """
        self._config = config
        # Reinitialize the converter with the new configuration
        self._converter = self._initialize_converter()

class DocumentProcessorFactory:
    """
    Factory for creating document processors.
    """
    @staticmethod
    def create_pdf_processor(config: Optional[DocumentConfig] = None) -> DoclingPDFProcessor:
        """
        Create a PDF document processor.
        """
        return DoclingPDFProcessor(config)

    @staticmethod
    def create_processor_with_defaults() -> DoclingPDFProcessor:
        """
        Create a PDF document processor with default configuration.
        """
        default_config = DocumentConfig(
            extract_tables=True,
            extract_images=True,
            ocr_enabled=True,
            max_pages=None,
        )
        return DoclingPDFProcessor(default_config)

def docling_process(file_path:str, config: Optional[DocumentConfig] = None) -> ProcessingResult:
    """
    Simplified function API for a single document processing. 
    """
    processor = DocumentProcessorFactory.create_pdf_processor(config)
    return processor.process(file_path)


if __name__ == "__main__":
    # Example 1: Using the simple function API (Facade)
    print("=" * 70)
    print("Example 1: Simple Function API")
    print("=" * 70)
    
    assets_dir = Path(__file__).parent.parent.parent / "assets"
    pdf_path = assets_dir / "2206.01062.pdf"
    
    if pdf_path.exists():
        result = docling_process(str(pdf_path))
        print(result)
        print(f"Content length: {len(result.content)} characters")
        print(f"Metadata: {result.metadata}")
    
    print("\n" + "=" * 70)
    print("Example 2: Function API with Custom Config")
    print("=" * 70)
    
    # Create custom configuration
    custom_config = DocumentConfig(
        extract_tables=True,
        extract_images=False,
        ocr_enabled=True
    )
    
    # Create processor using factory
    processor = DocumentProcessorFactory.create_pdf_processor(custom_config)
    
    # Process single file
    if pdf_path.exists():
        result = processor.process(str(pdf_path))
        print(f"Success: {result.success}")
        if result.success:
            print(f"Extracted {len(result.content)} characters")
            print(f"Pages: {result.metadata.get('num_pages', 'N/A')}")
    
    print("\n" + "=" * 70)
    print("Example 3: Batch Processing")
    print("=" * 70)
    
    # Process all PDFs in directory
    if assets_dir.exists():
        results = processor.process_directory(str(assets_dir))
        print(f"Processed {len(results)} files")
        for r in results:
            print(f"  - {r}")
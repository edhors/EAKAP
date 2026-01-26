from typing import List, Optional, Union
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


class TextProcessor:
    """
    Handles document loading and text chunking using LangChain loaders and splitters.
    
    Supports loading various file types (PDF, text, markdown) and configurable
    chunk size, overlap, and splitter types.
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        splitter_type: str = "recursive"
    ):
        """
        Initialize the TextProcessor with chunking parameters.
        
        Args:
            chunk_size: Maximum size of each text chunk (default: 1000)
            chunk_overlap: Number of characters to overlap between chunks (default: 200)
            splitter_type: Type of splitter to use (default: "recursive")
                          Currently only "recursive" is supported
        """
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap must be non-negative")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")
        
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitter_type = splitter_type
        
        # Initialize the splitter based on type
        if splitter_type == "recursive":
            self.splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                add_start_index=True
            )
        else:
            raise ValueError(
                f"Unsupported splitter_type: {splitter_type}. "
                "Currently only 'recursive' is supported."
            )
    
    def split_text(self, text: str) -> List[str]:
        """
        Split a single text string into chunks.
        
        Args:
            text: The text string to split
            
        Returns:
            List of text chunks as strings
            
        Raises:
            ValueError: If text is empty or None
        """
        if not text:
            raise ValueError("Text cannot be empty or None")
        
        if not isinstance(text, str):
            raise TypeError("Text must be a string")
        
        return self.splitter.split_text(text)
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split LangChain Document objects into chunks.
        
        Preserves metadata from original documents in the chunked documents.
        
        Args:
            documents: List of LangChain Document objects to split
            
        Returns:
            List of chunked Document objects with preserved metadata
            
        Raises:
            ValueError: If documents list is empty or None
        """
        if not documents:
            raise ValueError("Documents list cannot be empty or None")
        
        if not isinstance(documents, list):
            raise TypeError("Documents must be a list")
        
        return self.splitter.split_documents(documents)
    
    def load_file(
        self,
        file_path: Union[str, Path],
        file_type: Optional[str] = None,
        encoding: str = "utf-8"
    ) -> List[Document]:
        """
        Load a single file and return Document objects.
        
        Supports PDF, text, and markdown files. File type is auto-detected
        from extension if not specified.
        
        Args:
            file_path: Path to the file to load
            file_type: Type of file ("pdf", "text", "markdown"). If None, auto-detected from extension
            encoding: Encoding for text files (default: "utf-8")
        
        Returns:
            List of Document objects loaded from the file
        
        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If file type is unsupported or cannot be determined
            ImportError: If required package for the file type is not installed
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Auto-detect file type from extension if not provided
        if file_type is None:
            extension = file_path.suffix.lower()
            if extension == ".pdf":
                file_type = "pdf"
            elif extension in [".txt", ".text"]:
                file_type = "text"
            elif extension in [".md", ".markdown"]:
                file_type = "markdown"
            else:
                raise ValueError(
                    f"Cannot auto-detect file type for extension '{extension}'. "
                    f"Please specify file_type parameter. Supported types: pdf, text, markdown"
                )
        
        file_type = file_type.lower()
        
        try:
            if file_type == "pdf":
                return self._load_pdf(file_path)
            elif file_type == "text":
                return self._load_text(file_path, encoding)
            elif file_type == "markdown":
                return self._load_markdown(file_path)
            else:
                raise ValueError(
                    f"Unsupported file type: {file_type}. "
                    f"Supported types: pdf, text, markdown"
                )
        except ImportError as e:
            raise ImportError(
                f"Required package not installed for {file_type} files. {str(e)}"
            ) from e
    
    def load_directory(
        self,
        directory_path: Union[str, Path],
        glob_pattern: str = "**/*",
        loader_type: Optional[str] = None,
        show_progress: bool = False
    ) -> List[Document]:
        """
        Load multiple files from a directory.
        
        Args:
            directory_path: Path to the directory containing files
            glob_pattern: Glob pattern to match files (default: "**/*" for all files)
                         Examples: "**/*.pdf", "**/*.txt", "**/*.md"
            loader_type: Type of loader to use ("pdf", "text", "markdown").
                       If None, auto-detected from glob pattern or file extension
            show_progress: Whether to show loading progress (default: False)
        
        Returns:
            List of Document objects loaded from all matching files
        
        Raises:
            FileNotFoundError: If the directory doesn't exist
            ValueError: If loader_type is unsupported or cannot be determined
            ImportError: If required package for the loader type is not installed
        """
        directory_path = Path(directory_path)
        
        if not directory_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        if not directory_path.is_dir():
            raise ValueError(f"Path is not a directory: {directory_path}")
        
        # Auto-detect loader type from glob pattern if not provided
        if loader_type is None:
            if "*.pdf" in glob_pattern or glob_pattern.endswith(".pdf"):
                loader_type = "pdf"
            elif "*.txt" in glob_pattern or glob_pattern.endswith(".txt") or "*.text" in glob_pattern:
                loader_type = "text"
            elif "*.md" in glob_pattern or glob_pattern.endswith(".md") or "*.markdown" in glob_pattern:
                loader_type = "markdown"
            else:
                # Try to detect from first matching file
                matching_files = list(directory_path.glob(glob_pattern))
                if matching_files:
                    first_file = matching_files[0]
                    extension = first_file.suffix.lower()
                    if extension == ".pdf":
                        loader_type = "pdf"
                    elif extension in [".txt", ".text"]:
                        loader_type = "text"
                    elif extension in [".md", ".markdown"]:
                        loader_type = "markdown"
                    else:
                        raise ValueError(
                            f"Cannot auto-detect loader type from glob pattern '{glob_pattern}'. "
                            f"Please specify loader_type parameter. Supported types: pdf, text, markdown"
                        )
                else:
                    raise ValueError(
                        f"No files found matching pattern '{glob_pattern}' in {directory_path}"
                    )
        
        loader_type = loader_type.lower()
        
        try:
            from langchain_community.document_loaders import DirectoryLoader
            
            if loader_type == "pdf":
                from langchain_community.document_loaders import PyPDFLoader
                loader_cls = PyPDFLoader
            elif loader_type == "text":
                from langchain_community.document_loaders import TextLoader
                loader_cls = TextLoader
            elif loader_type == "markdown":
                from langchain_community.document_loaders import UnstructuredMarkdownLoader
                loader_cls = UnstructuredMarkdownLoader
            else:
                raise ValueError(
                    f"Unsupported loader type: {loader_type}. "
                    f"Supported types: pdf, text, markdown"
                )
            
            loader = DirectoryLoader(
                path=str(directory_path),
                glob=glob_pattern,
                loader_cls=loader_cls,
                show_progress=show_progress
            )
            
            return loader.load()
            
        except ImportError as e:
            raise ImportError(
                f"Required package not installed for {loader_type} files. {str(e)}"
            ) from e
    
    def load_and_split(
        self,
        source: Union[str, Path],
        source_type: str = "file",
        **load_kwargs
    ) -> List[Document]:
        """
        Load documents from a file or directory and automatically split them into chunks.
        
        Convenience method that combines loading and splitting in one step.
        
        Args:
            source: Path to file or directory
            source_type: Type of source ("file" or "directory", default: "file")
            **load_kwargs: Additional keyword arguments passed to load_file or load_directory
        
        Returns:
            List of chunked Document objects
        
        Raises:
            ValueError: If source_type is invalid
        """
        if source_type == "file":
            documents = self.load_file(source, **load_kwargs)
        elif source_type == "directory":
            documents = self.load_directory(source, **load_kwargs)
        else:
            raise ValueError(
                f"Invalid source_type: {source_type}. Must be 'file' or 'directory'"
            )
        
        return self.split_documents(documents)
    
    def _load_pdf(self, file_path: Path) -> List[Document]:
        """Load a PDF file."""
        try:
            from langchain_community.document_loaders import PyPDFLoader
        except ImportError:
            raise ImportError(
                "langchain-community package is required for PDF loading. "
                "Install it with: pip install langchain-community"
            )
        
        loader = PyPDFLoader(str(file_path))
        return loader.load()
    
    def _load_text(self, file_path: Path, encoding: str = "utf-8") -> List[Document]:
        """Load a text file."""
        try:
            from langchain_community.document_loaders import TextLoader
        except ImportError:
            raise ImportError(
                "langchain-community package is required for text file loading. "
                "Install it with: pip install langchain-community"
            )
        
        loader = TextLoader(str(file_path), encoding=encoding)
        return loader.load()
    
    def _load_markdown(self, file_path: Path) -> List[Document]:
        """Load a markdown file."""
        try:
            from langchain_community.document_loaders import UnstructuredMarkdownLoader
        except ImportError:
            raise ImportError(
                "langchain-community package is required for markdown loading. "
                "Install it with: pip install langchain-community"
            )
        
        loader = UnstructuredMarkdownLoader(str(file_path))
        return loader.load()

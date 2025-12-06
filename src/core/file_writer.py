"""Safe file and directory writing utilities for DevForge."""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class FileWriter:
    """Handles safe file and directory creation."""
    
    def __init__(self, dry_run: bool = False):
        """
        Initialize FileWriter.
        
        Args:
            dry_run: If True, don't actually write files, just log what would be written
        """
        self.dry_run = dry_run
        self.operations = []  # Track operations for dry-run reporting
    
    def create_directory(self, path: Path, exist_ok: bool = True) -> None:
        """
        Create a directory safely.
        
        Args:
            path: Directory path to create
            exist_ok: If True, don't raise error if directory exists
            
        Raises:
            OSError: If directory creation fails
        """
        if self.dry_run:
            logger.info(f"[DRY RUN] Would create directory: {path}")
            self.operations.append(("create_directory", str(path)))
            return
        
        try:
            path.mkdir(parents=True, exist_ok=exist_ok)
            logger.info(f"Created directory: {path}")
        except OSError as e:
            logger.error(f"Failed to create directory {path}: {e}")
            raise
    
    def write_file(
        self,
        path: Path,
        content: str,
        overwrite: bool = False
    ) -> None:
        """
        Write content to a file safely.
        
        Args:
            path: File path to write
            content: Content to write
            overwrite: If True, overwrite existing file. If False, raise error if file exists
            
        Raises:
            FileExistsError: If file exists and overwrite is False
            OSError: If file writing fails
        """
        if self.dry_run:
            logger.info(f"[DRY RUN] Would write file: {path}")
            self.operations.append(("write_file", str(path)))
            return
        
        # Check if file exists
        if path.exists() and not overwrite:
            raise FileExistsError(
                f"File already exists: {path}. Use overwrite=True to replace it."
            )
        
        # Ensure parent directory exists
        parent = path.parent
        if parent and not parent.exists():
            self.create_directory(parent, exist_ok=True)
        
        try:
            # Write file with UTF-8 encoding
            path.write_text(content, encoding='utf-8')
            logger.info(f"Wrote file: {path}")
        except OSError as e:
            logger.error(f"Failed to write file {path}: {e}")
            raise
    
    def get_operations_summary(self) -> list:
        """
        Get summary of operations that would be performed (useful for dry-run).
        
        Returns:
            List of operation tuples
        """
        return self.operations.copy()


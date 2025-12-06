"""Tests for FileWriter."""

import pytest
from pathlib import Path

from src.core.file_writer import FileWriter


class TestFileWriter:
    """Test FileWriter functionality."""
    
    def test_create_directory(self, tmp_path):
        """create_directory should create folder."""
        writer = FileWriter(dry_run=False)
        test_dir = tmp_path / "test_dir"
        
        writer.create_directory(test_dir)
        
        assert test_dir.exists()
        assert test_dir.is_dir()
    
    def test_write_file(self, tmp_path):
        """write_file should write content."""
        writer = FileWriter(dry_run=False)
        test_file = tmp_path / "test.txt"
        content = "test content"
        
        writer.write_file(test_file, content)
        
        assert test_file.exists()
        assert test_file.read_text() == content
    
    def test_overwrite_protection(self, tmp_path):
        """write_file should protect against overwrite."""
        writer = FileWriter(dry_run=False)
        test_file = tmp_path / "test.txt"
        test_file.write_text("original")
        
        with pytest.raises(FileExistsError):
            writer.write_file(test_file, "new content", overwrite=False)
        
        # Original content should remain
        assert test_file.read_text() == "original"
    
    def test_overwrite_allowed(self, tmp_path):
        """write_file should overwrite when allowed."""
        writer = FileWriter(dry_run=False)
        test_file = tmp_path / "test.txt"
        test_file.write_text("original")
        
        writer.write_file(test_file, "new content", overwrite=True)
        
        assert test_file.read_text() == "new content"
    
    def test_dry_run_does_not_create_files(self, tmp_path):
        """Dry-run should NOT create files."""
        writer = FileWriter(dry_run=True)
        test_file = tmp_path / "test.txt"
        test_dir = tmp_path / "test_dir"
        
        writer.create_directory(test_dir)
        writer.write_file(test_file, "content")
        
        assert not test_file.exists()
        assert not test_dir.exists()
    
    def test_dry_run_tracks_operations(self, tmp_path):
        """Dry-run should track operations."""
        writer = FileWriter(dry_run=True)
        test_file = tmp_path / "test.txt"
        test_dir = tmp_path / "test_dir"
        
        writer.create_directory(test_dir)
        writer.write_file(test_file, "content")
        
        operations = writer.get_operations_summary()
        assert len(operations) == 2
        assert ("create_directory", str(test_dir)) in operations
        assert ("write_file", str(test_file)) in operations
    
    def test_write_file_creates_parent_dirs(self, tmp_path):
        """write_file should create parent directories."""
        writer = FileWriter(dry_run=False)
        test_file = tmp_path / "parent" / "child" / "test.txt"
        
        writer.write_file(test_file, "content")
        
        assert test_file.exists()
        assert test_file.parent.exists()



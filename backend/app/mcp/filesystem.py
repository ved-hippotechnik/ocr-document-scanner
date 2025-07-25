"""
Filesystem MCP Server

Provides file system operations and management for document processing.
"""

import os
import json
import shutil
import logging
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from dataclasses import dataclass, field
import mimetypes

logger = logging.getLogger(__name__)


@dataclass
class FileInfo:
    """Information about a file"""
    path: str
    name: str
    size: int
    modified: datetime
    created: datetime
    mime_type: str
    checksum: str
    is_directory: bool = False
    permissions: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FileOperation:
    """Record of a file operation"""
    operation_id: str
    operation_type: str  # create, read, update, delete, move, copy
    source_path: str
    target_path: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    status: str = "pending"
    result: Optional[Any] = None
    error: Optional[str] = None


class FilesystemMCP:
    """
    Filesystem MCP Server
    
    Provides secure file system operations for document processing.
    """
    
    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path) if base_path else Path.cwd() / "mcp_storage"
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        self.operations_log: List[FileOperation] = []
        self.file_cache: Dict[str, FileInfo] = {}
        
        # Security settings
        self.allowed_extensions = {
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff',
            '.pdf', '.txt', '.json', '.xml', '.csv',
            '.doc', '.docx', '.xls', '.xlsx'
        }
        
        self.max_file_size = 100 * 1024 * 1024  # 100MB
        
        logger.info(f"FilesystemMCP initialized with base path: {self.base_path}")
    
    def _validate_path(self, path: Union[str, Path]) -> Path:
        """Validate and normalize a path"""
        path = Path(path)
        
        # Ensure path is within base directory
        try:
            resolved = (self.base_path / path).resolve()
            resolved.relative_to(self.base_path)
        except ValueError:
            raise ValueError(f"Path {path} is outside base directory")
        
        return resolved
    
    def _get_file_checksum(self, file_path: Path) -> str:
        """Calculate file checksum"""
        sha256_hash = hashlib.sha256()
        
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating checksum for {file_path}: {str(e)}")
            return ""
    
    def _get_file_info(self, path: Path) -> FileInfo:
        """Get detailed information about a file"""
        stat = path.stat()
        
        return FileInfo(
            path=str(path.relative_to(self.base_path)),
            name=path.name,
            size=stat.st_size if path.is_file() else 0,
            modified=datetime.fromtimestamp(stat.st_mtime),
            created=datetime.fromtimestamp(stat.st_ctime),
            mime_type=mimetypes.guess_type(str(path))[0] or "application/octet-stream",
            checksum=self._get_file_checksum(path) if path.is_file() else "",
            is_directory=path.is_dir(),
            permissions=oct(stat.st_mode)[-3:],
            metadata={
                "extension": path.suffix,
                "parent": str(path.parent.relative_to(self.base_path))
            }
        )
    
    def create_directory(self, path: str, parents: bool = True) -> bool:
        """Create a directory"""
        import uuid
        operation = FileOperation(
            operation_id=str(uuid.uuid4()),
            operation_type="create",
            source_path=path
        )
        
        try:
            dir_path = self._validate_path(path)
            dir_path.mkdir(parents=parents, exist_ok=True)
            
            operation.status = "completed"
            operation.result = {"created": str(dir_path)}
            
            logger.info(f"Created directory: {dir_path}")
            return True
            
        except Exception as e:
            operation.status = "failed"
            operation.error = str(e)
            logger.error(f"Failed to create directory {path}: {str(e)}")
            return False
        finally:
            self.operations_log.append(operation)
    
    def write_file(self, path: str, content: Union[str, bytes], 
                   metadata: Optional[Dict[str, Any]] = None) -> Optional[FileInfo]:
        """Write content to a file"""
        import uuid
        operation = FileOperation(
            operation_id=str(uuid.uuid4()),
            operation_type="create",
            source_path=path
        )
        
        try:
            file_path = self._validate_path(path)
            
            # Check extension
            if file_path.suffix.lower() not in self.allowed_extensions:
                raise ValueError(f"File extension {file_path.suffix} not allowed")
            
            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content
            if isinstance(content, str):
                file_path.write_text(content, encoding='utf-8')
            else:
                file_path.write_bytes(content)
            
            # Check file size
            if file_path.stat().st_size > self.max_file_size:
                file_path.unlink()
                raise ValueError(f"File size exceeds maximum allowed size of {self.max_file_size} bytes")
            
            # Get file info
            file_info = self._get_file_info(file_path)
            if metadata:
                file_info.metadata.update(metadata)
            
            # Update cache
            self.file_cache[str(file_path)] = file_info
            
            operation.status = "completed"
            operation.result = {"file_info": file_info}
            
            logger.info(f"Wrote file: {file_path}")
            return file_info
            
        except Exception as e:
            operation.status = "failed"
            operation.error = str(e)
            logger.error(f"Failed to write file {path}: {str(e)}")
            return None
        finally:
            self.operations_log.append(operation)
    
    def read_file(self, path: str, encoding: str = 'utf-8') -> Optional[Union[str, bytes]]:
        """Read content from a file"""
        import uuid
        operation = FileOperation(
            operation_id=str(uuid.uuid4()),
            operation_type="read",
            source_path=path
        )
        
        try:
            file_path = self._validate_path(path)
            
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {path}")
            
            if not file_path.is_file():
                raise ValueError(f"Path is not a file: {path}")
            
            # Read content
            if encoding:
                content = file_path.read_text(encoding=encoding)
            else:
                content = file_path.read_bytes()
            
            operation.status = "completed"
            operation.result = {"size": len(content)}
            
            logger.debug(f"Read file: {file_path}")
            return content
            
        except Exception as e:
            operation.status = "failed"
            operation.error = str(e)
            logger.error(f"Failed to read file {path}: {str(e)}")
            return None
        finally:
            self.operations_log.append(operation)
    
    def list_directory(self, path: str = "", pattern: str = "*", 
                      recursive: bool = False) -> List[FileInfo]:
        """List files in a directory"""
        try:
            dir_path = self._validate_path(path)
            
            if not dir_path.exists():
                raise FileNotFoundError(f"Directory not found: {path}")
            
            if not dir_path.is_dir():
                raise ValueError(f"Path is not a directory: {path}")
            
            files = []
            
            if recursive:
                for file_path in dir_path.rglob(pattern):
                    files.append(self._get_file_info(file_path))
            else:
                for file_path in dir_path.glob(pattern):
                    files.append(self._get_file_info(file_path))
            
            logger.debug(f"Listed {len(files)} files in {dir_path}")
            return files
            
        except Exception as e:
            logger.error(f"Failed to list directory {path}: {str(e)}")
            return []
    
    def move_file(self, source: str, target: str) -> bool:
        """Move a file or directory"""
        import uuid
        operation = FileOperation(
            operation_id=str(uuid.uuid4()),
            operation_type="move",
            source_path=source,
            target_path=target
        )
        
        try:
            source_path = self._validate_path(source)
            target_path = self._validate_path(target)
            
            if not source_path.exists():
                raise FileNotFoundError(f"Source not found: {source}")
            
            # Ensure target parent exists
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Move file
            shutil.move(str(source_path), str(target_path))
            
            # Update cache
            if str(source_path) in self.file_cache:
                del self.file_cache[str(source_path)]
            
            operation.status = "completed"
            operation.result = {"moved_to": str(target_path)}
            
            logger.info(f"Moved {source_path} to {target_path}")
            return True
            
        except Exception as e:
            operation.status = "failed"
            operation.error = str(e)
            logger.error(f"Failed to move file from {source} to {target}: {str(e)}")
            return False
        finally:
            self.operations_log.append(operation)
    
    def copy_file(self, source: str, target: str) -> bool:
        """Copy a file or directory"""
        import uuid
        operation = FileOperation(
            operation_id=str(uuid.uuid4()),
            operation_type="copy",
            source_path=source,
            target_path=target
        )
        
        try:
            source_path = self._validate_path(source)
            target_path = self._validate_path(target)
            
            if not source_path.exists():
                raise FileNotFoundError(f"Source not found: {source}")
            
            # Ensure target parent exists
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file or directory
            if source_path.is_file():
                shutil.copy2(str(source_path), str(target_path))
            else:
                shutil.copytree(str(source_path), str(target_path))
            
            operation.status = "completed"
            operation.result = {"copied_to": str(target_path)}
            
            logger.info(f"Copied {source_path} to {target_path}")
            return True
            
        except Exception as e:
            operation.status = "failed"
            operation.error = str(e)
            logger.error(f"Failed to copy file from {source} to {target}: {str(e)}")
            return False
        finally:
            self.operations_log.append(operation)
    
    def delete_file(self, path: str, force: bool = False) -> bool:
        """Delete a file or directory"""
        import uuid
        operation = FileOperation(
            operation_id=str(uuid.uuid4()),
            operation_type="delete",
            source_path=path
        )
        
        try:
            file_path = self._validate_path(path)
            
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {path}")
            
            # Delete file or directory
            if file_path.is_file():
                file_path.unlink()
            else:
                if force:
                    shutil.rmtree(str(file_path))
                else:
                    file_path.rmdir()  # Only works if directory is empty
            
            # Update cache
            if str(file_path) in self.file_cache:
                del self.file_cache[str(file_path)]
            
            operation.status = "completed"
            operation.result = {"deleted": str(file_path)}
            
            logger.info(f"Deleted: {file_path}")
            return True
            
        except Exception as e:
            operation.status = "failed"
            operation.error = str(e)
            logger.error(f"Failed to delete {path}: {str(e)}")
            return False
        finally:
            self.operations_log.append(operation)
    
    def get_file_info(self, path: str) -> Optional[FileInfo]:
        """Get information about a file"""
        try:
            file_path = self._validate_path(path)
            
            if not file_path.exists():
                return None
            
            # Check cache first
            if str(file_path) in self.file_cache:
                cached_info = self.file_cache[str(file_path)]
                # Verify file hasn't changed
                stat = file_path.stat()
                if cached_info.modified == datetime.fromtimestamp(stat.st_mtime):
                    return cached_info
            
            # Get fresh info
            file_info = self._get_file_info(file_path)
            self.file_cache[str(file_path)] = file_info
            
            return file_info
            
        except Exception as e:
            logger.error(f"Failed to get file info for {path}: {str(e)}")
            return None
    
    def search_files(self, query: str, search_in: str = "", 
                    file_types: Optional[List[str]] = None) -> List[FileInfo]:
        """Search for files matching criteria"""
        results = []
        search_path = self._validate_path(search_in) if search_in else self.base_path
        
        try:
            for file_path in search_path.rglob("*"):
                if file_path.is_file():
                    # Check file type
                    if file_types and file_path.suffix.lower() not in file_types:
                        continue
                    
                    # Check if query matches filename
                    if query.lower() in file_path.name.lower():
                        results.append(self._get_file_info(file_path))
            
            logger.info(f"Search found {len(results)} files matching '{query}'")
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            return []
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        total_size = 0
        file_count = 0
        dir_count = 0
        file_types = {}
        
        try:
            for path in self.base_path.rglob("*"):
                if path.is_file():
                    file_count += 1
                    size = path.stat().st_size
                    total_size += size
                    
                    ext = path.suffix.lower()
                    if ext not in file_types:
                        file_types[ext] = {"count": 0, "total_size": 0}
                    file_types[ext]["count"] += 1
                    file_types[ext]["total_size"] += size
                    
                elif path.is_dir():
                    dir_count += 1
            
            return {
                "base_path": str(self.base_path),
                "total_size": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "file_count": file_count,
                "directory_count": dir_count,
                "file_types": file_types,
                "operations_count": len(self.operations_log),
                "cache_size": len(self.file_cache)
            }
            
        except Exception as e:
            logger.error(f"Failed to get storage stats: {str(e)}")
            return {}
    
    def export_operations_log(self) -> List[Dict[str, Any]]:
        """Export operations log"""
        return [
            {
                "operation_id": op.operation_id,
                "type": op.operation_type,
                "source": op.source_path,
                "target": op.target_path,
                "timestamp": op.timestamp.isoformat(),
                "status": op.status,
                "error": op.error
            }
            for op in self.operations_log
        ]
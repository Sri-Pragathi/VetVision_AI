"""Storage abstraction service supporting local and extensible cloud storage."""
import os
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO, Union
from flask import current_app


class BaseImageStorage(ABC):
    """Abstract interface for image binary storage."""

    @abstractmethod
    def save_file(self, file_source: Union[BinaryIO, bytes], relative_path: str) -> str:
        """Persist a file and return its storage key / path identifier."""
        pass

    @abstractmethod
    def get_absolute_path(self, storage_key: str) -> str:
        """Return the accessible local filesystem path for processing."""
        pass

    @abstractmethod
    def delete_file(self, storage_key: str) -> bool:
        """Remove a file from storage."""
        pass

    @abstractmethod
    def file_exists(self, storage_key: str) -> bool:
        """Check whether a stored file exists."""
        pass


class LocalStorageService(BaseImageStorage):
    """Local filesystem storage implementation with directory isolation and path traversal guards."""

    def __init__(self, base_folder: Union[str, Path, None] = None):
        self._custom_base = Path(base_folder) if base_folder else None

    @property
    def base_dir(self) -> Path:
        """Resolve root upload directory."""
        if self._custom_base:
            base = self._custom_base
        elif current_app and "UPLOAD_FOLDER" in current_app.config:
            base = Path(current_app.config["UPLOAD_FOLDER"])
        else:
            base = Path(os.getenv("UPLOAD_FOLDER", "uploads"))
        base.mkdir(parents=True, exist_ok=True)
        return base.resolve()

    def _resolve_safe_path(self, relative_path: str) -> Path:
        """Resolve path and verify that it remains within the base upload directory."""
        # Sanitize relative path (remove leading slashes / backslashes)
        clean_rel = relative_path.lstrip("/\\")
        target_path = (self.base_dir / clean_rel).resolve()
        # Path traversal guard
        if not str(target_path).startswith(str(self.base_dir)):
            raise ValueError(f"Path traversal detected: {relative_path}")
        return target_path

    def save_file(self, file_source: Union[BinaryIO, bytes], relative_path: str) -> str:
        """Save file to local filesystem."""
        target_path = self._resolve_safe_path(relative_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(file_source, bytes):
            with open(target_path, "wb") as f:
                f.write(file_source)
        else:
            file_source.seek(0)
            with open(target_path, "wb") as f:
                shutil.copyfileobj(file_source, f)

        # Return standardized relative key
        return relative_path.replace("\\", "/").lstrip("/")

    def get_absolute_path(self, storage_key: str) -> str:
        """Return absolute path for computer vision analysis."""
        return str(self._resolve_safe_path(storage_key))

    def delete_file(self, storage_key: str) -> bool:
        """Safely delete file from disk."""
        try:
            target_path = self._resolve_safe_path(storage_key)
            if target_path.is_file():
                target_path.unlink()
                return True
            return False
        except Exception:
            return False

    def file_exists(self, storage_key: str) -> bool:
        """Check whether the file exists on disk."""
        try:
            target_path = self._resolve_safe_path(storage_key)
            return target_path.is_file()
        except Exception:
            return False

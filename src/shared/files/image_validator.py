# s3_storage.py
from __future__ import annotations

import os 
from typing import Any, BinaryIO, Sequence

class ImageValidator:
    def validate(
        self,
        images: Sequence[Any],
        *,
        max_size_bytes: int | None = None,
        allowed_extensions: set[str] | None = None,
        allowed_mime_types: set[str] | None = None,
        require_magic_bytes: bool = True,
    ) -> None:
        if not images:
            raise ValueError("images cannot be empty")

        allowed_extensions = allowed_extensions or {".jpg", ".jpeg", ".png", ".webp"}
        allowed_mime_types = allowed_mime_types or {"image/jpeg", "image/png", "image/webp"}

        for idx, item in enumerate(images):
            fileobj, filename, content_type = self._extract(item)

            if not hasattr(fileobj, "read"):
                raise TypeError(f"Item at index {idx} is not readable")
            if not hasattr(fileobj, "seek") or not hasattr(fileobj, "tell"):
                raise TypeError(f"Item at index {idx} must be seekable (seek/tell required)")

            # Size check
            pos = fileobj.tell()
            fileobj.seek(0, os.SEEK_END)
            size = fileobj.tell()
            fileobj.seek(pos)

            if max_size_bytes is not None and size > max_size_bytes:
                raise ValueError(f"Image at index {idx} exceeds max size ({size} > {max_size_bytes})")

            # Extension check
            if filename:
                _, ext = os.path.splitext(filename)
                ext = ext.lower()
                if ext not in allowed_extensions:
                    raise ValueError(f"Image at index {idx} has invalid extension '{ext}'")

            # MIME check (UploadFile only; do not fully trust it)
            if content_type and content_type not in allowed_mime_types:
                raise ValueError(f"Image at index {idx} has invalid MIME type '{content_type}'")

            # Magic bytes check (stronger than MIME/ext)
            if require_magic_bytes:
                self._validate_magic(fileobj, idx)

    def _extract(self, item: Any) -> tuple[BinaryIO, str | None, str | None]:
        # Supports FastAPI UploadFile or raw file-like objects
        if hasattr(item, "file"):
            fileobj = item.file
            filename = getattr(item, "filename", None)
            content_type = getattr(item, "content_type", None)
            return fileobj, filename, content_type

        fileobj = item
        filename = getattr(item, "name", None)
        return fileobj, filename, None

    def _validate_magic(self, fileobj: BinaryIO, idx: int) -> None:
        pos = fileobj.tell()
        try:
            fileobj.seek(0)
            head = fileobj.read(16) or b""
        finally:
            fileobj.seek(pos)

        # JPEG: FF D8 FF
        if head[:3] == b"\xFF\xD8\xFF":
            return
        # PNG: 89 50 4E 47 0D 0A 1A 0A
        if head[:8] == b"\x89PNG\r\n\x1a\n":
            return
        # WEBP: RIFF....WEBP
        if len(head) >= 12 and head[:4] == b"RIFF" and head[8:12] == b"WEBP":
            return

        raise ValueError(f"Image at index {idx} does not look like a valid JPG/PNG/WEBP by signature")

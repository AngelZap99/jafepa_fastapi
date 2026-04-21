from __future__ import annotations

import os
from contextvars import ContextVar, Token
from pathlib import Path
from typing import Any, BinaryIO, Sequence
from urllib.parse import urlparse
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import UploadFile

load_dotenv()

_current_request_base_url: ContextVar[str | None] = ContextVar(
    "current_request_base_url",
    default=None,
)


def get_media_root() -> Path:
    configured = os.getenv("MEDIA_ROOT", "storage/media")
    path = Path(configured)
    if not path.is_absolute():
        path = Path.cwd() / path
    path.mkdir(parents=True, exist_ok=True)
    return path.resolve()


def get_media_public_base_url() -> str | None:
    value = os.getenv("MEDIA_PUBLIC_BASE_URL") or os.getenv("PUBLIC_BASE_URL")
    if not value:
        return None
    return value.rstrip("/")


def set_current_request_base_url(value: str | None) -> Token[str | None]:
    normalized = value.rstrip("/") if value else None
    return _current_request_base_url.set(normalized)


def reset_current_request_base_url(token: Token[str | None]) -> None:
    _current_request_base_url.reset(token)


def get_current_request_base_url() -> str | None:
    return _current_request_base_url.get()


def get_media_url_prefix() -> str:
    prefix = (os.getenv("MEDIA_URL_PREFIX") or "/api/media").strip()
    if not prefix.startswith("/"):
        prefix = f"/{prefix}"
    return prefix.rstrip("/") or "/api/media"


def get_media_url_prefixes() -> list[str]:
    prefixes = [get_media_url_prefix(), "/media", "/api/media"]
    out: list[str] = []
    for prefix in prefixes:
        normalized = prefix.strip()
        if not normalized.startswith("/"):
            normalized = f"/{normalized}"
        normalized = normalized.rstrip("/") or "/"
        if normalized not in out:
            out.append(normalized)
    return out


def resolve_media_path(file_path_or_url: str | None) -> Path | None:
    if not file_path_or_url:
        return None

    value = str(file_path_or_url).strip()
    if not value:
        return None

    media_root = get_media_root()
    media_prefixes = get_media_url_prefixes()

    if value.startswith(("http://", "https://")):
        parsed = urlparse(value)
        relative_key = None
        for media_prefix in media_prefixes:
            if parsed.path.startswith(f"{media_prefix}/"):
                relative_key = parsed.path[len(media_prefix) :].lstrip("/")
                break
        if relative_key is None:
            return None
    elif value.startswith("/"):
        relative_key = None
        for media_prefix in media_prefixes:
            if value.startswith(f"{media_prefix}/"):
                relative_key = value[len(media_prefix) :].lstrip("/")
                break
        if relative_key is None:
            return None
    else:
        relative_key = value.lstrip("/")

    if not relative_key:
        return None

    candidate = (media_root / relative_key).resolve()
    try:
        candidate.relative_to(media_root)
    except ValueError:
        return None
    return candidate


def normalize_media_reference(file_path_or_url: str | None) -> str | None:
    if not file_path_or_url:
        return None

    value = str(file_path_or_url).strip()
    if not value:
        return None

    path = resolve_media_path(value)
    if path is None:
        return value

    return str(path.relative_to(get_media_root())).replace(os.sep, "/")


def build_public_media_url(
    file_path_or_url: str | None,
    *,
    base_url: str | None = None,
) -> str | None:
    normalized = normalize_media_reference(file_path_or_url)
    if not normalized:
        return None

    parsed = urlparse(normalized)
    if parsed.scheme and parsed.netloc:
        return normalized

    effective_base_url = base_url or get_current_request_base_url()
    handler = LocalFileHandler(public_base_url=effective_base_url)
    return handler._build_public_url(normalized, base_url=effective_base_url)


class LocalFileHandler:
    """Stores public files on local disk and returns a public URL."""

    def __init__(
        self,
        media_root: Path | None = None,
        media_url_prefix: str | None = None,
        public_base_url: str | None = None,
    ) -> None:
        self.media_root = (media_root or get_media_root()).resolve()
        self.media_root.mkdir(parents=True, exist_ok=True)
        self.media_url_prefix = media_url_prefix or get_media_url_prefix()
        self.public_base_url = (
            public_base_url.rstrip("/")
            if public_base_url
            else get_media_public_base_url()
        )

    def _safe_key(self, prefix: str, filename: str | None = None) -> str:
        normalized_prefix = prefix.strip().strip("/")
        normalized_prefix = f"{normalized_prefix}/" if normalized_prefix else ""

        ext = ""
        if filename:
            _, ext = os.path.splitext(filename)
            ext = ext.lower()

        return f"{normalized_prefix}{uuid4()}{ext}"

    def _build_public_url(self, key: str, *, base_url: str | None = None) -> str:
        prefix = self.media_url_prefix.rstrip("/")
        cleaned_key = key.lstrip("/")

        if self.public_base_url:
            return f"{self.public_base_url}{prefix}/{cleaned_key}"
        if base_url:
            return f"{base_url.rstrip('/')}{prefix}/{cleaned_key}"
        return f"{prefix}/{cleaned_key}"

    def _normalize_key(self, file_path_or_url: str) -> str:
        path = resolve_media_path(file_path_or_url)
        if path is None:
            value = str(file_path_or_url).strip().lstrip("/")
            if not value:
                raise ValueError("La ruta o URL del archivo no puede estar vacía")
            return value

        return str(path.relative_to(self.media_root)).replace(os.sep, "/")

    def _rewind(self, fileobj: BinaryIO) -> None:
        if hasattr(fileobj, "seek"):
            try:
                fileobj.seek(0)
            except Exception:
                pass

    def upload_fileobj(
        self,
        fileobj: BinaryIO,
        *,
        object_key: str | None = None,
        filename: str | None = None,
        content_type: str | None = None,
        make_public: bool | None = None,
        prefix: str = "files",
        base_url: str | None = None,
    ) -> tuple[str, str]:
        del content_type, make_public

        key = object_key.lstrip("/") if object_key else self._safe_key(prefix, filename)
        destination = (self.media_root / key).resolve()
        try:
            destination.relative_to(self.media_root)
        except ValueError as exc:
            raise RuntimeError("La ruta del archivo local no es válida") from exc

        destination.parent.mkdir(parents=True, exist_ok=True)
        self._rewind(fileobj)
        with destination.open("wb") as target:
            while True:
                chunk = fileobj.read(1024 * 1024)
                if not chunk:
                    break
                target.write(chunk)

        return key, self._build_public_url(key, base_url=base_url)

    def upload_uploadfile(
        self,
        upload: UploadFile,
        *,
        object_key: str | None = None,
        make_public: bool | None = None,
        prefix: str = "files",
        base_url: str | None = None,
    ) -> tuple[str, str]:
        return self.upload_fileobj(
            fileobj=upload.file,
            object_key=object_key,
            filename=upload.filename,
            content_type=upload.content_type,
            make_public=make_public,
            prefix=prefix,
            base_url=base_url,
        )

    def upload_multiple_files(
        self,
        files: Sequence[BinaryIO],
        *,
        object_keys: Sequence[str] | None = None,
        content_types: Sequence[str | None] | None = None,
        make_public: bool | None = None,
        prefix: str = "files",
        base_url: str | None = None,
    ) -> list[tuple[str, str]]:
        if object_keys is not None and len(files) != len(object_keys):
            raise ValueError(
                "La cantidad de archivos y claves de objeto debe coincidir"
            )
        if content_types is not None and len(content_types) != len(files):
            raise ValueError(
                "La cantidad de tipos de contenido debe coincidir con la cantidad de archivos"
            )

        uploaded: list[tuple[str, str]] = []
        for index, fileobj in enumerate(files):
            key = object_keys[index] if object_keys is not None else None
            uploaded.append(
                self.upload_fileobj(
                    fileobj=fileobj,
                    object_key=key,
                    content_type=content_types[index] if content_types else None,
                    make_public=make_public,
                    prefix=prefix,
                    base_url=base_url,
                )
            )
        return uploaded

    def delete_file(self, file_path_or_url: str) -> bool:
        try:
            key = self._normalize_key(file_path_or_url)
            target = (self.media_root / key).resolve()
            target.relative_to(self.media_root)
        except (ValueError, FileNotFoundError):
            return False

        if not target.exists():
            return False

        try:
            target.unlink()
        except OSError:
            return False

        current = target.parent
        while current != self.media_root:
            try:
                current.rmdir()
            except OSError:
                break
            current = current.parent
        return True

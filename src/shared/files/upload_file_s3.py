# s3_storage.py
from __future__ import annotations

import os
from typing import Any, BinaryIO, Sequence
from urllib.parse import urlparse
from uuid import uuid4

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from dotenv import load_dotenv
from fastapi import UploadFile

load_dotenv()  # Loads .env into os.environ


class S3FileHandler:
    """Simple S3 handler for PUBLIC buckets using credentials from .env."""

    def __init__(
        self,
        bucket_name: str | None = None,
        bucket_base_url: str | None = None,
        region_name: str | None = None,
        public_default: bool = True,
        use_acl: bool = False,
    ) -> None:
        self.bucket_name = bucket_name or os.getenv("AWS_S3_BUCKET")
        if not self.bucket_name:
            raise ValueError("Missing env AWS_S3_BUCKET")

        self.region_name = region_name or os.getenv("AWS_REGION", "us-east-1")

        base_url = bucket_base_url or os.getenv("AWS_S3_BUCKET_URL")
        self.bucket_base_url = base_url.rstrip("/") if base_url else None

        self.public_default = public_default
        self.use_acl = use_acl

        access_key = os.getenv("AWS_ACCESS_KEY_ID")
        secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        if not access_key or not secret_key:
            raise ValueError(
                "Missing AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY in .env"
            )

        self.s3_client = boto3.client(
            "s3",
            region_name=self.region_name,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(
                signature_version="s3v4",
                retries={"max_attempts": 10, "mode": "standard"},
                connect_timeout=5,
                read_timeout=60,
            ),
        )

    def _build_public_url(self, key: str) -> str:
        if self.bucket_base_url:
            return f"{self.bucket_base_url}/{key}"

        if self.region_name == "us-east-1":
            return f"https://{self.bucket_name}.s3.amazonaws.com/{key}"
        return f"https://{self.bucket_name}.s3.{self.region_name}.amazonaws.com/{key}"

    def _normalize_s3_key(self, file_path_or_url: str) -> str:
        if not file_path_or_url:
            raise ValueError("file_path_or_url cannot be empty")

        value = file_path_or_url.strip()

        if self.bucket_base_url and value.startswith(self.bucket_base_url):
            return value[len(self.bucket_base_url) :].lstrip("/")

        if value.startswith(("http://", "https://")):
            parsed = urlparse(value)
            path = parsed.path.lstrip("/")

            # Path-style: .../{bucket}/{key}
            if path.startswith(f"{self.bucket_name}/"):
                return path[len(self.bucket_name) + 1 :]

            return path

        return value.lstrip("/")

    def _safe_key(self, prefix: str, filename: str | None = None) -> str:
        prefix = prefix.strip().strip("/")
        prefix = f"{prefix}/" if prefix else ""

        ext = ""
        if filename:
            _, ext = os.path.splitext(filename)
            ext = ext.lower()

        return f"{prefix}{uuid4()}{ext}"

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
        make_public: bool | None = None,  # None => uses self.public_default
        prefix: str = "files",
    ) -> tuple[str, str]:
        key = (
            object_key.lstrip("/")
            if object_key
            else self._safe_key(prefix=prefix, filename=filename)
        )
        public = self.public_default if make_public is None else make_public

        extra_args: dict[str, Any] = {}
        if content_type:
            extra_args["ContentType"] = content_type
        if self.use_acl and public:
            extra_args["ACL"] = "public-read"

        try:
            self._rewind(fileobj)
            self.s3_client.upload_fileobj(
                Fileobj=fileobj,
                Bucket=self.bucket_name,
                Key=key,
                ExtraArgs=extra_args or None,
            )
            return key, self._build_public_url(key)
        except (BotoCoreError, ClientError) as exc:
            raise RuntimeError(f"Failed to upload file to S3: {exc}") from exc

    def upload_uploadfile(
        self,
        upload: UploadFile,
        *,
        object_key: str | None = None,
        make_public: bool | None = None,
        prefix: str = "files",
    ) -> tuple[str, str]:
        return self.upload_fileobj(
            fileobj=upload.file,
            object_key=object_key,
            filename=upload.filename,
            content_type=upload.content_type,
            make_public=make_public,
            prefix=prefix,
        )

    def upload_multiple_files(
        self,
        files: Sequence[BinaryIO],
        *,
        object_keys: Sequence[str] | None = None,
        content_types: Sequence[str | None] | None = None,
        make_public: bool | None = None,
        prefix: str = "files",
    ) -> list[tuple[str, str]]:
        if object_keys is not None and len(files) != len(object_keys):
            raise ValueError("files and object_keys must have the same length")
        if content_types is not None and len(content_types) != len(files):
            raise ValueError("content_types must have the same length as files")

        out: list[tuple[str, str]] = []
        for i, f in enumerate(files):
            key = object_keys[i] if object_keys is not None else None
            ctype = content_types[i] if content_types is not None else None
            out.append(
                self.upload_fileobj(
                    fileobj=f,
                    object_key=key,
                    content_type=ctype,
                    make_public=make_public,
                    prefix=prefix,
                )
            )
        return out

    def delete_file(self, file_path_or_url: str) -> bool:
        try:
            key = self._normalize_s3_key(file_path_or_url)
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            return True
        except (BotoCoreError, ClientError, ValueError):
            return False

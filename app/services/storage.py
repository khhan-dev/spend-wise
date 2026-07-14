"""증빙 이미지 저장소.

MVP는 로컬 파일시스템. 운영 전환 시 S3Storage로 교체(동일 인터페이스).
key는 서버가 생성한 단순 파일명(UUID)만 허용해 경로 조작(path traversal)을 차단한다.
"""

import os
import uuid
from functools import lru_cache

from app.core.config import settings

_EXT_BY_CONTENT_TYPE = {
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/png": "png",
    "image/tiff": "tiff",
    "application/pdf": "pdf",
}


def ext_for(content_type: str | None, filename: str | None) -> str:
    if content_type and content_type.lower() in _EXT_BY_CONTENT_TYPE:
        return _EXT_BY_CONTENT_TYPE[content_type.lower()]
    if filename and "." in filename:
        ext = filename.rsplit(".", 1)[-1].lower()
        if ext in {"jpg", "jpeg", "png", "tiff", "tif", "pdf"}:
            return "jpg" if ext == "jpeg" else ext
    return "bin"


class LocalStorage:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir

    @staticmethod
    def _is_safe_key(key: str) -> bool:
        return bool(key) and "/" not in key and "\\" not in key and ".." not in key

    def save(self, data: bytes, ext: str) -> str:
        os.makedirs(self.base_dir, exist_ok=True)
        key = f"{uuid.uuid4().hex}.{ext.lstrip('.')}"
        with open(os.path.join(self.base_dir, key), "wb") as f:
            f.write(data)
        return key

    def path(self, key: str) -> str:
        return os.path.join(self.base_dir, key)

    def exists(self, key: str) -> bool:
        return self._is_safe_key(key) and os.path.isfile(self.path(key))

    def load(self, key: str) -> bytes:
        with open(self.path(key), "rb") as f:
            return f.read()


@lru_cache
def get_storage() -> LocalStorage:
    return LocalStorage(settings.upload_dir)

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Dict

import requests
from flask_github import GitHub

from ose.utils import get_file

DEFAULT_LIFE_TIME = 60 * 60 * 24

@dataclass
class CacheEntry:
    filename: str
    updated: datetime
    expires: datetime
    id: str


class FileCache:
    lifetime: int
    cache_dir: str

    _cache_file: str
    _cache: Dict[str, CacheEntry]

    def __init__(self, cache_dir: str, life_time: int = DEFAULT_LIFE_TIME):
        self.lifetime = life_time
        self.cache_dir = cache_dir
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir, exist_ok=True)

        self._cache_file = os.path.join(self.cache_dir, "cache.json")
        self._cache = {}

    def _save_cache(self):
        with open(self._cache_file, "w") as f:
            json.dump(self._cache, f, indent=2)

    def _load_cache(self):
        if os.path.exists(self._cache_file):
            with open(self._cache_file, "r") as f:
                data = json.load(f)
                self._cache = {k: CacheEntry(id=k,
                                             filename=v["filename"],
                                             updated=datetime.fromisoformat(v["updated"]),
                                             expires=datetime.fromisoformat(v["expires"])) for k, v in data.items()}

    def _store_cache_entry(self, id: str, basename: str, content: bytes, lifetime: int):
        file_path = os.path.join(self.cache_dir, f"{id}-{basename}")
        with open(file_path, "wb") as f:
            f.write(content)

        updated = datetime.now()
        expires = updated + timedelta(seconds=lifetime)
        self._cache[id] = CacheEntry(filename=basename, updated=updated, expires=expires, id=id)
        self._save_cache()

    def _retrieve_from_cache(self, id: str):
        entry = self._cache[id]
        if entry.expires > datetime.now():
            with open(os.path.join(self.cache_dir, f"{id}-{entry.filename}"), "rb") as f:
                return f.read()
        else:
            del self._cache[id]
        return None

    def get_from_github(self, gh: GitHub, repo: str, path: str, lifetime: Optional[int] = None) -> bytes:
        self._load_cache()

        lifetime = lifetime or self.lifetime

        id = "GH_" + hashlib.md5((repo + "$" + path).encode()).hexdigest()
        basename = os.path.basename(path)

        if id in self._cache:
            content = self._retrieve_from_cache(id)
            if content is not None:
                return content

        content = get_file(gh, repo, path)
        self._store_cache_entry(id, basename, content, lifetime)

        return content

    def get_from_url(self, url: str, lifetime: Optional[int] = None) -> bytes:
        self._load_cache()

        lifetime = lifetime or self.lifetime

        id = "URL_" + hashlib.md5(url.encode()).hexdigest()
        basename = os.path.basename(url)

        if id in self._cache:
            content = self._retrieve_from_cache(id)
            if content is not None:
                return content

        response = requests.get(url)
        response.raise_for_status()
        content = response.content
        self._store_cache_entry(id, basename, content, lifetime)

        return content

    def cleanup(self):

        to_delete = []
        for id, entry in self._cache.items():
            if entry.expires <= datetime.now():
                to_delete.append(id)
        for id in to_delete:
            file_path = os.path.join(self.cache_dir, f"{id}-{self._cache[id].filename}")
            if os.path.exists(file_path):
                os.remove(file_path)
            del self._cache[id]
        self._save_cache()

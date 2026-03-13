import hashlib
from pathlib import Path


def calc_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def save_file(storage_dir: str, filename: str, content: bytes) -> str:
    Path(storage_dir).mkdir(parents=True, exist_ok=True)
    target = Path(storage_dir) / filename
    target.write_bytes(content)
    return str(target)

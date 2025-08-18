from __future__ import annotations
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Tuple

ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = ROOT / "artifacts"
CACHE = ARTIFACTS / "cache"


def _json_dumps_canonical(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def config_hash(config: Dict[str, Any]) -> str:
    """Return a stable SHA256 hash for a configuration dict."""
    s = _json_dumps_canonical(config)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def load_config(path: Path | str | None, cli_overrides: Dict[str, Any] | None = None) -> Tuple[Dict[str, Any], str]:
    """Load JSON config and merge CLI overrides; returns (config, hash)."""
    data: Dict[str, Any] = {}
    if path:
        p = Path(path)
        data = json.loads(p.read_text()) if p.exists() else {}
    if cli_overrides:
        # Shallow merge is fine for our simple cases
        data.update({k: v for k, v in cli_overrides.items() if v is not None})
    h = config_hash(data)
    return data, h


def cache_path_for(hash_str: str, name: str) -> Path:
    """Return an artifacts/cache path for a given hash and artifact name (without extension)."""
    CACHE.mkdir(parents=True, exist_ok=True)
    return CACHE / f"{name}-{hash_str}.npz"


@dataclass
class ROI:
    extent: float = 0.2
    z_extent: float = 0.2
    n: int = 41
    nz: int = 21

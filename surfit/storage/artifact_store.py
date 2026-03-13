from __future__ import annotations

from abc import ABC, abstractmethod
import json
from pathlib import Path
from typing import Any


class ArtifactStore(ABC):
    @abstractmethod
    def save(self, artifact_id: str, payload: dict[str, Any]) -> str:
        raise NotImplementedError


class FileArtifactStore(ArtifactStore):
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, artifact_id: str, payload: dict[str, Any]) -> str:
        target = self.root / f"{artifact_id}.json"
        target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return str(target)


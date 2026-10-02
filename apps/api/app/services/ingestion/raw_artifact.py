from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RawArtifact:
    raw_bytes: bytes
    content_type: str
    source_uri: str
    file_format: str

    @property
    def reference_id(self) -> str:
        return hashlib.sha256(self.raw_bytes).hexdigest()


def attach_raw_artifact(payload: dict[str, Any], artifact: RawArtifact) -> dict[str, Any]:
    wrapped = dict(payload)
    wrapped["_raw_artifact"] = artifact
    wrapped["_raw_artifact_ref"] = artifact.reference_id
    return wrapped

"""Embedding generation via Microsoft Foundry Local.

Uses Foundry Local's OpenAI-compatible HTTP endpoint rather than its Python
SDK. The SDK (`foundry_local_sdk`) only ever reported a `generic-cpu` model
variant on this machine and could not load the cached CUDA variant, even
though the CLI confirmed the GPU variant was cached and loadable. The HTTP
endpoint serves the GPU variant correctly. The port is discovered via
`foundry status -o json` rather than hardcoded, since it is not stable
across service restarts.
"""

import hashlib
import json
import subprocess
import urllib.request
from pathlib import Path

import numpy as np

MODEL_ID = "qwen3-embedding-0.6b-cuda-gpu"

# The catalog reports context_length=32768 tokens, but in practice the
# CUDA embedding endpoint returns HTTP 500 past roughly 1500-2000 words
# (measured empirically). Truncate with a safety margin and log affected
# chunks rather than fail or silently trust the advertised limit.
MAX_WORDS = 1200


def discover_endpoint() -> str:
    """Finds the address Foundry Local's service is currently running on."""
    result = subprocess.run(
        ["foundry", "status", "-o", "json"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    status = json.loads(result.stdout)
    service = status.get("service", {})
    if not service.get("ready"):
        raise RuntimeError("Foundry Local service is not ready. Run `foundry server start`.")
    urls = service.get("webUrls") or []
    if not urls:
        raise RuntimeError("Could not find a Foundry Local endpoint.")
    return urls[0].rstrip("/")


class Embedder:
    def __init__(self, cache_dir: Path, batch_size: int = 16, model_id: str = MODEL_ID):
        self.endpoint = discover_endpoint()
        self.model_id = model_id
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.batch_size = batch_size
        self.dim: int | None = None
        self.truncated_count = 0

    def _cache_path(self, text: str) -> Path:
        key = hashlib.sha256(f"{self.model_id}:{text}".encode("utf-8")).hexdigest()[:16]
        return self.cache_dir / f"emb_{key}.npy"

    def _truncate(self, text: str) -> str:
        words = text.split()
        if len(words) <= MAX_WORDS:
            return text
        self.truncated_count += 1
        return " ".join(words[:MAX_WORDS])

    def _request(self, inputs: list[str]) -> list[list[float]]:
        inputs = [self._truncate(t) for t in inputs]
        payload = json.dumps({"model": self.model_id, "input": inputs}).encode("utf-8")
        req = urllib.request.Request(
            f"{self.endpoint}/v1/embeddings",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=300) as resp:
            body = json.loads(resp.read())
        return [item["embedding"] for item in body["data"]]

    def embed(self, texts: list[str]) -> np.ndarray:
        """Returns an L2-normalized embedding matrix, using a disk cache."""
        results: list[np.ndarray | None] = [None] * len(texts)
        pending_idx = []
        pending_texts = []

        for i, text in enumerate(texts):
            path = self._cache_path(text)
            if path.exists():
                results[i] = np.load(path)
            else:
                pending_idx.append(i)
                pending_texts.append(text)

        for start in range(0, len(pending_texts), self.batch_size):
            batch = pending_texts[start : start + self.batch_size]
            batch_idx = pending_idx[start : start + self.batch_size]
            vectors = self._request(batch)
            for i, vec in zip(batch_idx, vectors):
                arr = np.asarray(vec, dtype=np.float32)
                norm = np.linalg.norm(arr)
                if norm > 0:
                    arr = arr / norm
                results[i] = arr
                np.save(self._cache_path(texts[i]), arr)
            print(f"  embedded {start + len(batch)}/{len(pending_texts)} new texts", flush=True)

        matrix = np.vstack(results)
        self.dim = matrix.shape[1]
        return matrix


if __name__ == "__main__":
    import sys
    import time

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import CACHE_DIR

    embedder = Embedder(CACHE_DIR)
    print(f"Foundry Local endpoint: {embedder.endpoint}")
    print(f"Model: {embedder.model_id}")

    probe = [f"sample text {i} machine learning and deep learning" for i in range(20)]
    t0 = time.time()
    vecs = embedder.embed(probe)
    elapsed = time.time() - t0
    print(f"20 texts: {elapsed:.2f}s -> estimated for 900 texts: {elapsed / 20 * 900:.1f}s")
    print(f"Vector shape: {vecs.shape}, norm: {np.linalg.norm(vecs[0]):.4f}")

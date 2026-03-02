import faiss
import numpy as np
from pathlib import Path


class FaissChunkIndex:
    def __init__(self, index_dir: Path):
        self.index_dir = index_dir
        self.index_path = index_dir / "index.faiss"
        self.ids_path = index_dir / "chunk_ids.txt"
        self.index = None
        self.chunk_ids = []

    def load_or_create(self, dim):
        self.index_dir.mkdir(parents=True, exist_ok=True)

        if self.index_path.exists():
            self.index = faiss.read_index(str(self.index_path))
            self.chunk_ids = self.ids_path.read_text().splitlines()
        else:
            self.index = faiss.IndexFlatIP(dim)
            self.chunk_ids = []

    def add(self, embeddings, ids):
        self.index.add(embeddings)
        self.chunk_ids.extend(ids)

    def search(self, vector, top_k):
        scores, indices = self.index.search(
            np.array([vector], dtype="float32"),
            top_k,
        )

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.chunk_ids):
                results.append((self.chunk_ids[idx], float(score)))

        return results

    def save(self):
        faiss.write_index(self.index, str(self.index_path))
        self.ids_path.write_text("\n".join(self.chunk_ids))
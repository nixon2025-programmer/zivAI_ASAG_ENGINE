import numpy as np
from sentence_transformers import SentenceTransformer


class SentenceTransformerEmbedder:
    def __init__(self, model_name: str):
        self.model = SentenceTransformer(model_name)

    def embed_texts(self, texts):
        vecs = self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return np.asarray(vecs, dtype="float32")

    def embed_query(self, query):
        return self.embed_texts([query])[0]
from pathlib import Path
import uuid
from sqlalchemy.orm import Session

from .models import ResourceChunk
from .chunking import chunk_document
from .embeddings import SentenceTransformerEmbedder
from .faiss_index import FaissChunkIndex
from .extractors import (
    extract_pdf,
    extract_docx,
    extract_image_with_mindocr,
    MindOCRRunner,
)
from asag_engine.config import settings


class ResourceIntelligenceService:

    def __init__(self):
        self.embedder = SentenceTransformerEmbedder(
            "sentence-transformers/all-MiniLM-L6-v2"
        )

        self.index = FaissChunkIndex(
            Path("data/indexes/resources_faiss")
        )

        self.index_initialized = False

        self.mindocr = None
        if hasattr(settings, "mindocr_home") and settings.mindocr_home:
            try:
                self.mindocr = MindOCRRunner(settings.mindocr_home)
            except Exception:
                self.mindocr = None

    def ingest_file(self, db: Session, file_path: Path, original_filename: str):

        doc_id = uuid.uuid4().hex

        extracted = self._extract(doc_id, original_filename, file_path)

        chunks = chunk_document(
            doc_id=doc_id,
            filename=original_filename,
            file_type=extracted["file_type"],
            pages=extracted["pages"],
        )

        if not chunks:
            return {"message": "No extractable text"}

        texts = [c["chunk_text"] for c in chunks]
        vectors = self.embedder.embed_texts(texts)

        if not self.index_initialized:
            self.index.load_or_create(vectors.shape[1])
            self.index_initialized = True

        self.index.add(vectors, [c["chunk_id"] for c in chunks])
        self.index.save()

        for c in chunks:
            db.add(ResourceChunk(**c))

        db.commit()

        return {
            "doc_id": doc_id,
            "chunks": len(chunks),
        }

    def search(self, db: Session, query: str, top_k=5):

        if not self.index_initialized:
            return {"results": [], "citations": []}

        qv = self.embedder.embed_query(query)
        hits = self.index.search(qv, top_k)

        results = []
        citations = []

        for chunk_id, score in hits:
            chunk = db.query(ResourceChunk).filter_by(
                chunk_id=chunk_id
            ).first()

            if not chunk:
                continue

            results.append({
                "score": score,
                "text": chunk.chunk_text,
            })

            citations.append({
                "filename": chunk.filename,
                "page": chunk.page_number,
                "snippet": chunk.snippet,
            })

        return {
            "results": results,
            "citations": citations,
        }

    def _extract(self, doc_id, filename, path: Path):

        suffix = path.suffix.lower()

        if suffix == ".pdf":
            return extract_pdf(
                doc_id,
                filename,
                path,
                mindocr=self.mindocr,
            )

        if suffix == ".docx":
            return extract_docx(
                doc_id,
                filename,
                path,
            )

        if suffix in [".png", ".jpg", ".jpeg"]:
            return extract_image_with_mindocr(
                doc_id,
                filename,
                path,
                self.mindocr,
            )

        raise ValueError("Unsupported file type")
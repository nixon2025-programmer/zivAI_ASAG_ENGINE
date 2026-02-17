import os
import glob
import argparse
import logging
import orjson
from typing import Dict, Any, List

from asag_engine.ingest.pdf_loaders import load_pdf
from asag_engine.ingest.chunking import chunk_docs

log = logging.getLogger("asag.ingest")

def _infer_metadata(file_path: str, doc_type: str) -> Dict[str, Any]:
    # Very simple metadata parser: extend later (year, paper, q numbers).
    base = os.path.basename(file_path)
    return {
        "source_file": base,
        "doc_type": doc_type,  # "exam" or "markscheme"
    }

def _dump_jsonl(path: str, records: List[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        for r in records:
            f.write(orjson.dumps(r))
            f.write(b"\n")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--exams_dir", required=True)
    parser.add_argument("--markschemes_dir", required=True)
    args = parser.parse_args()

    exams_paths = sorted(glob.glob(os.path.join(args.exams_dir, "*.pdf")))
    ms_paths = sorted(glob.glob(os.path.join(args.markschemes_dir, "*.pdf")))

    processed_dir = "data/processed"
    exams_out = os.path.join(processed_dir, "exams.jsonl")
    ms_out = os.path.join(processed_dir, "markschemes.jsonl")

    exams_records: List[Dict[str, Any]] = []
    ms_records: List[Dict[str, Any]] = []

    for p in exams_paths:
        docs = load_pdf(p)
        chunks = chunk_docs(docs)
        meta = _infer_metadata(p, "exam")
        for c in chunks:
            exams_records.append({
                "text": c.page_content,
                "metadata": {**meta, **(c.metadata or {})},
            })
        log.info(f"Ingested exam: {p} -> {len(chunks)} chunks")

    for p in ms_paths:
        docs = load_pdf(p)
        chunks = chunk_docs(docs)
        meta = _infer_metadata(p, "markscheme")
        for c in chunks:
            ms_records.append({
                "text": c.page_content,
                "metadata": {**meta, **(c.metadata or {})},
            })
        log.info(f"Ingested markscheme: {p} -> {len(chunks)} chunks")

    _dump_jsonl(exams_out, exams_records)
    _dump_jsonl(ms_out, ms_records)

    log.info(f"Wrote: {exams_out} ({len(exams_records)} records)")
    log.info(f"Wrote: {ms_out} ({len(ms_records)} records)")

if __name__ == "__main__":
    main()

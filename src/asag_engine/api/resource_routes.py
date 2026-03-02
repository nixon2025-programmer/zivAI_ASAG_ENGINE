from flask import Blueprint, request, jsonify
from pathlib import Path
import tempfile

from asag_engine.db.session import get_db
from asag_engine.resource_intelligence.service import ResourceIntelligenceService

bp_resources = Blueprint("resources", __name__, url_prefix="/api/v1/resources")

service = ResourceIntelligenceService()


@bp_resources.post("/upload")
def upload_resource():
    db = next(get_db())

    if "file" not in request.files:
        return jsonify({"error": "Missing file"}), 400

    f = request.files["file"]

    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / f.filename
        f.save(str(path))

        result = service.ingest_file(db, path, f.filename)
        return jsonify(result)


@bp_resources.post("/search")
def search_resources():
    db = next(get_db())

    data = request.get_json()
    query = data.get("query")
    top_k = data.get("top_k", 5)

    result = service.search(db, query, top_k)
    return jsonify(result)
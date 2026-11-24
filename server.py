from flask import Flask, jsonify, request, send_from_directory, session, has_request_context
from pathlib import Path
from werkzeug.utils import secure_filename
from pypdf import PdfReader
from docx import Document
import json
import os
import random
import re
import secrets
import uuid
from datetime import datetime
from hashlib import sha256

BASE = Path(__file__).resolve().parent
UPLOADS = BASE / "uploads"
DATA_FILE = BASE / "bca_data.json"
DATA_DIR = Path(os.environ.get("DATA_DIR", BASE / "data"))
ACADEMIC_CONTENT_FILE = BASE / "academic_content.json"
PUBLIC_DEPLOY = os.environ.get("PUBLIC_DEPLOY", "").lower() == "true"
PAPER_SUBJECTS = {
    "UCC1A": "Fundamentals of Digital Computers",
    "UCC2A": "Programming in C",
    "URC1A": "Mathematics I",
    "URC2A": "Mathematics II",
    "UEB1A": "English I",
    "UEB2A": "English II",
    "UCC3C": "Numerical and Statistical Methods",
    "UNC3A": "Financial Accounting",
}
if not PUBLIC_DEPLOY:
    UPLOADS.mkdir(exist_ok=True)

app = Flask(__name__, static_folder=str(BASE), static_url_path="")
app.secret_key = os.environ.get("APP_SECRET_KEY") or "local-development-only-key"
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=PUBLIC_DEPLOY,
)
if PUBLIC_DEPLOY and not os.environ.get("APP_SECRET_KEY"):
    raise RuntimeError("APP_SECRET_KEY must be configured for public deployment")


def current_storage_id():
    if not PUBLIC_DEPLOY or not has_request_context():
        return None
    visitor_id = session.get("visitor_id")
    if not visitor_id:
        visitor_id = secrets.token_urlsafe(32)
        session["visitor_id"] = visitor_id
    return sha256(visitor_id.encode("utf-8")).hexdigest()


def current_data_file():
    storage_id = current_storage_id()
    return DATA_DIR / f"{storage_id}.json" if storage_id else DATA_FILE


def current_upload_dir():
    storage_id = current_storage_id()
    return DATA_DIR / "uploads" / storage_id if storage_id else UPLOADS


def default_data():
    return {
        "profile": {"name": "", "semester": "I", "examDate": ""},
        "answers": [],
        "practiceAttempts": [],
        "mockAttempts": [],
        "weakAreas": [],
        "uploadedDocuments": [],
        "examDraft": None,
        "readingProgress": {},
        "bookmarks": [],
    }


def load_data():
    data_file = current_data_file()
    if not data_file.exists():
        return default_data()
    try:
        data = json.loads(data_file.read_text(encoding="utf-8"))
        defaults = default_data()
        for key, value in defaults.items():
            data.setdefault(key, value)
        return data
    except json.JSONDecodeError:
        return default_data()


def save_data(data):
    data_file = current_data_file()
    data_file.parent.mkdir(parents=True, exist_ok=True)
    data_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def academic_inventory_dir():
    local = BASE / "academic_inventory"
    return local if local.is_dir() else BASE.parent / "academic_inventory"


@app.route("/")
def index():
    portal = BASE / "portal.html"
    return send_from_directory(str(BASE), "portal.html" if portal.exists() else "index.html")


@app.before_request
def prevent_private_file_serving():
    parts = Path(request.path.lstrip("/")).parts
    if parts and (
        parts[0] in {"uploads", "data", "__pycache__"}
        or parts[0] in {"bca_data.json", ".env"}
        or request.path.startswith("/.env.")
    ):
        return jsonify({"error": "Not found"}), 404


@app.route("/dashboard")
@app.route("/onboarding")
@app.route("/semesters")
@app.route("/subjects")
@app.route("/library")
@app.route("/notes")
@app.route("/pyq")
@app.route("/questions")
@app.route("/practice")
@app.route("/flashcards")
@app.route("/exam")
@app.route("/study-planner")
@app.route("/progress")
@app.route("/search")
def app_pages():
    return index()


@app.route("/<path:path>")
def assets(path):
    target = BASE / path
    if target.is_file():
        return send_from_directory(str(BASE), path)
    return jsonify({"error": "Not found"}), 404


@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "service": "BCA Study & Exam Hub"})


def academic_content():
    if not ACADEMIC_CONTENT_FILE.is_file():
        return None, (jsonify({"error": "Academic source extraction is unavailable"}), 503)
    try:
        content = json.loads(ACADEMIC_CONTENT_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None, (jsonify({"error": "Academic source index is invalid"}), 500)
    return content, None


@app.route("/api/academic-documents")
def academic_documents():
    content, error = academic_content()
    if error:
        return error
    documents = []
    for document in content.get("documents", []):
        subjects = {}
        for block in document.get("blocks", []):
            code = block.get("subject_code")
            if code and code not in subjects:
                subjects[code] = {
                    "code": code,
                    "name": block.get("subject"),
                    "semester": block.get("semester"),
                }
        documents.append({
            key: document.get(key)
            for key in ("id", "filename", "document_type", "word_count", "block_count", "pagination")
        } | {"subjects": list(subjects.values())})
    return jsonify(documents)


@app.route("/api/academic-document/<document_id>")
def academic_document(document_id):
    content, error = academic_content()
    if error:
        return error
    document = next(
        (item for item in content.get("documents", []) if item.get("id") == document_id),
        None,
    )
    if not document:
        return jsonify({"error": "Academic source document was not found"}), 404
    try:
        start = max(0, int(request.args.get("start", "0")))
        limit = min(250, max(1, int(request.args.get("limit", "180"))))
    except ValueError:
        return jsonify({"error": "Invalid source range"}), 400
    subject_code = request.args.get("subject_code", "").upper()
    all_blocks = document.get("blocks", [])
    indexed_blocks = [
        (index, block) for index, block in enumerate(all_blocks)
        if not subject_code or block.get("subject_code") == subject_code
    ]
    blocks = [
        {**block, "_index": index}
        for index, block in indexed_blocks[start:start + limit]
    ]
    return jsonify({
        "document": {
            key: document.get(key)
            for key in ("id", "filename", "document_type", "word_count", "block_count", "pagination")
        },
        "blocks": blocks,
        "start": start,
        "next": start + limit if start + limit < len(indexed_blocks) else None,
        "previous": max(0, start - limit) if start > 0 else None,
        "total": len(indexed_blocks),
    })


@app.route("/api/search")
def search():
    query = request.args.get("q", "").strip()
    if len(query) < 2:
        return jsonify({"error": "Search needs at least two characters"}), 400
    terms = [term for term in re.findall(r"[\w'-]+", query.casefold()) if term]
    if not terms:
        return jsonify({"results": []})
    try:
        limit = min(80, max(1, int(request.args.get("limit", "40"))))
    except ValueError:
        return jsonify({"error": "Invalid search limit"}), 400
    content, error = academic_content()
    if error:
        return error
    results = []
    phrase = query.casefold()
    for document in content.get("documents", []):
        for index, block in enumerate(document.get("blocks", [])):
            text = block.get("text", "")
            lowered = text.casefold()
            if not all(term in lowered for term in terms):
                continue
            start = max(0, lowered.find(phrase) - 100) if phrase in lowered else 0
            snippet = text[start:start + 260]
            results.append({
                "kind": "source",
                "document_id": document["id"],
                "filename": document["filename"],
                "block_index": index,
                "source_location": block.get("source_location"),
                "page": block.get("page"),
                "semester": block.get("semester"),
                "subject": block.get("subject"),
                "subject_code": block.get("subject_code"),
                "unit": block.get("unit"),
                "snippet": snippet,
                "score": lowered.count(phrase) * 3 + sum(lowered.count(term) for term in terms),
            })
    questions_path = BASE / "pyq_questions.json"
    if questions_path.is_file():
        try:
            question_data = json.loads(questions_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            question_data = {"questions": []}
        for question in question_data.get("questions", []):
            text = question.get("question", "")
            lowered = text.casefold()
            if all(term in lowered for term in terms):
                results.append({
                    "kind": "pyq",
                    "question": text,
                    "paper_code": question.get("paper_code"),
                    "source_file": question.get("source_pdf", question.get("source_file")),
                    "source_url": question.get("source_url"),
                    "score": lowered.count(phrase) * 3 + sum(lowered.count(term) for term in terms),
                })
    results.sort(key=lambda result: result["score"], reverse=True)
    return jsonify({"query": query, "results": results[:limit]})


@app.route("/api/reading-state", methods=["GET", "PUT"])
def reading_state():
    data = load_data()
    if request.method == "GET":
        document_id = request.args.get("document_id", "")
        return jsonify(data["readingProgress"].get(document_id, {"block_index": 0}))
    payload = request.get_json(silent=True) or {}
    document_id = str(payload.get("document_id", ""))
    try:
        block_index = max(0, int(payload.get("block_index", 0)))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid reading position"}), 400
    content, error = academic_content()
    if error:
        return error
    if not any(item.get("id") == document_id for item in content.get("documents", [])):
        return jsonify({"error": "Academic source document was not found"}), 404
    data["readingProgress"][document_id] = {
        "block_index": block_index,
        "updated_at": datetime.utcnow().isoformat() + "Z",
    }
    save_data(data)
    return jsonify(data["readingProgress"][document_id])


@app.route("/api/bookmarks", methods=["GET", "POST", "DELETE"])
def bookmarks():
    data = load_data()
    if request.method == "GET":
        return jsonify(data["bookmarks"])
    if request.method == "DELETE":
        document_id = request.args.get("document_id", "")
        try:
            block_index = int(request.args.get("block_index", "-1"))
        except ValueError:
            return jsonify({"error": "Invalid bookmark position"}), 400
        data["bookmarks"] = [
            item for item in data["bookmarks"]
            if not (item.get("document_id") == document_id and item.get("block_index") == block_index)
        ]
        save_data(data)
        return jsonify({"status": "removed"})
    payload = request.get_json(silent=True) or {}
    document_id = str(payload.get("document_id", ""))
    try:
        block_index = int(payload.get("block_index", -1))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid bookmark position"}), 400
    content, error = academic_content()
    if error:
        return error
    document = next(
        (item for item in content.get("documents", []) if item.get("id") == document_id),
        None,
    )
    if not document or block_index < 0 or block_index >= len(document.get("blocks", [])):
        return jsonify({"error": "Bookmark source position was not found"}), 404
    bookmark = {
        "id": str(uuid.uuid4()),
        "document_id": document_id,
        "filename": document["filename"],
        "block_index": block_index,
        "source_location": document["blocks"][block_index].get("source_location"),
        "note": str(payload.get("note", ""))[:240],
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
    existing = next(
        (item for item in data["bookmarks"]
         if item.get("document_id") == document_id and item.get("block_index") == block_index),
        None,
    )
    if existing:
        existing.update(bookmark, id=existing["id"])
        bookmark = existing
    else:
        data["bookmarks"].append(bookmark)
    save_data(data)
    return jsonify(bookmark)


@app.route("/api/questions")
def questions():
    source = BASE / "pyq_questions.json"
    if not source.exists():
        return jsonify({"papers": [], "questions": [], "error": "PYQ extraction is not available"}), 503
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return jsonify({"error": "PYQ question index is invalid"}), 500
    index_path = academic_inventory_dir() / "pyq_index.json"
    packaged_sources = BASE / "pyq_papers"
    if index_path.exists():
        try:
            paper_index = json.loads(index_path.read_text(encoding="utf-8"))
            by_name = {Path(item["file"]).stem.lower(): item for item in paper_index if item.get("status") == "ok"}
            for question in payload.get("questions", []):
                matched = by_name.get(Path(question["source_file"]).stem.lower())
                if matched:
                    question["source_pdf"] = matched["file"]
                    question["source_url"] = "/api/pyq-file/" + matched["file"]
                else:
                    packaged = packaged_sources / Path(question["source_file"]).name
                    if packaged.is_file():
                        question["source_pdf"] = packaged.name
                        question["source_url"] = "/api/pyq-file/" + packaged.name
        except (json.JSONDecodeError, KeyError):
            pass
    return jsonify(payload)


@app.route("/api/pyq-file/<path:filename>")
def pyq_file(filename):
    packaged = BASE / "pyq_papers" / Path(filename).name
    if packaged.is_file():
        return send_from_directory(str(packaged.parent), packaged.name, as_attachment=False)
    inventory = academic_inventory_dir()
    index_path = inventory / "pyq_index.json"
    if not index_path.exists():
        return jsonify({"error": "PYQ source index is unavailable"}), 404
    items = json.loads(index_path.read_text(encoding="utf-8"))
    match = next((item for item in items if item.get("file", "").lower() == Path(filename).name.lower()), None)
    if not match:
        return jsonify({"error": "PYQ source was not found"}), 404
    source = Path(match.get("path", ""))
    if not source.is_file():
        source = next((item for item in inventory.rglob(Path(match["file"]).name) if item.is_file()), None)
    if source is None or not source.is_file():
        return jsonify({"error": "PYQ source file is missing"}), 404
    return send_from_directory(str(source.parent), source.name, as_attachment=False)


@app.route("/api/library")
def library():
    data = load_data()
    inventory = academic_inventory_dir()
    sources = []
    for code in ("SUCA101", "SUCA102", "SUCA103", "SUCA104", "SUCA105", "SUCA106",
                 "SUCA201A", "SUCA201B", "SUCA202", "SUCA203", "SUCA204", "SUCA205",
                 "SFCE11", "SFCE12", "SFEN11", "SFEN12"):
        text_path = inventory / f"{code}.txt"
        if text_path.is_file():
            sources.append({"name": f"{code} course book text", "code": code, "type": "TXT", "source": "Provided course book"})
    return jsonify({"uploads": data.get("uploadedDocuments", []), "courseBooks": sources})


@app.route("/api/source-text/<code>")
def source_text(code):
    if not code.isalnum():
        return jsonify({"error": "Invalid course code"}), 400
    source = academic_inventory_dir() / f"{code.upper()}.txt"
    if source.is_file():
        return jsonify({"code": code.upper(), "text": source.read_text(encoding="utf-8")})
    content, error = academic_content()
    if error:
        return error
    excerpts = [
        block["text"]
        for document in content.get("documents", [])
        for block in document.get("blocks", [])
        if block.get("subject_code") == code.upper()
    ]
    if not excerpts:
        return jsonify({"error": "Course text is not available"}), 404
    return jsonify({"code": code.upper(), "text": "\n".join(excerpts), "source": "Provided academic DOCX notebooks"})


@app.route("/api/document/<path:filename>")
def uploaded_document(filename):
    data = load_data()
    name = Path(filename).name
    if not any(item.get("name") == name for item in data.get("uploadedDocuments", [])):
        return jsonify({"error": "Document not found"}), 404
    upload_dir = current_upload_dir()
    path = upload_dir / name
    if not path.is_file():
        return jsonify({"error": "Stored document is missing"}), 404
    return send_from_directory(str(upload_dir), name, as_attachment=False)


@app.route("/api/document-text/<path:filename>")
def uploaded_document_text(filename):
    data = load_data()
    name = Path(filename).name
    if not any(item.get("name") == name for item in data.get("uploadedDocuments", [])):
        return jsonify({"error": "Document not found"}), 404
    text_path = (current_upload_dir() / name).with_suffix(".txt")
    if not text_path.is_file():
        return jsonify({"error": "No extracted text exists for this document"}), 404
    return jsonify({"name": name, "text": text_path.read_text(encoding="utf-8")})


@app.route("/api/exam-draft", methods=["GET", "PUT", "DELETE"])
def exam_draft():
    data = load_data()
    if request.method == "PUT":
        data["examDraft"] = request.get_json(silent=True) or {}
        save_data(data)
    elif request.method == "DELETE":
        data["examDraft"] = None
        save_data(data)
    return jsonify(data.get("examDraft"))


@app.route("/api/profile", methods=["GET", "PUT"])
def profile():
    data = load_data()
    if request.method == "PUT":
        data["profile"].update(request.get_json(silent=True) or {})
        save_data(data)
    return jsonify(data["profile"])


@app.route("/api/practice-attempt", methods=["POST"])
def save_practice_attempt():
    payload = request.get_json(silent=True) or {}
    data = load_data()
    attempt = {
        "subject": payload.get("subject", ""),
        "question": payload.get("question", ""),
        "answer": payload.get("answer", ""),
        "marks": payload.get("marks", ""),
        "timestamp": payload.get("timestamp"),
    }
    data["practiceAttempts"].append(attempt)
    save_data(data)
    return jsonify({"status": "saved", "attemptCount": len(data["practiceAttempts"])})


@app.route("/api/answer", methods=["POST"])
def save_answer():
    payload = request.get_json(silent=True) or {}
    data = load_data()
    data["answers"].append(payload)
    save_data(data)
    return jsonify({"status": "saved", "answerCount": len(data["answers"])})


@app.route("/api/mock", methods=["POST"])
def save_mock():
    payload = request.get_json(silent=True) or {}
    data = load_data()
    answers = payload.get("answers", [])
    earned = 0
    possible = 0
    details = []
    for item in answers:
        maximum = max(1, int(item.get("marks", 2) or 2))
        question_text = str(item.get("question", "")).lower()
        answer_text = str(item.get("answer", "")).lower()
        expected = set(word for word in question_text.split() if len(word) > 4)
        coverage = len(expected.intersection(answer_text.split())) / max(1, len(expected))
        length_points = min(1.0, len(answer_text.split()) / max(20, maximum * 8))
        score = round(maximum * min(1.0, coverage * 0.65 + length_points * 0.35), 1)
        earned += score
        possible += maximum
        details.append({**item, "earned": score, "possible": maximum})
    result = {
        "title": payload.get("title", "University Mock Examination"),
        "answers": details,
        "earned": earned,
        "possible": possible,
        "score": round(earned / possible * 100) if possible else 0,
        "timestamp": payload.get("timestamp") or datetime.utcnow().isoformat() + "Z",
        "feedbackNote": "Automated practice estimate based on answer relevance and completeness; not official university marking.",
    }
    data["weakAreas"] = data.get("weakAreas", [])
    for answer in details:
        if answer["earned"] < answer["possible"] * 0.5:
            data["weakAreas"].append({
                "subject": PAPER_SUBJECTS.get(
                    str(answer.get("subject", "")).upper(), answer.get("subject", "Mixed")
                ),
                "topic": answer.get("topic", answer.get("question", "Review answer")),
                "errors": 1,
                "source": "mock",
            })
    data["weakAreas"] = data["weakAreas"][-20:]
    data["mockAttempts"].append(result)
    data["examDraft"] = None
    save_data(data)
    return jsonify({"status": "saved", "attemptCount": len(data["mockAttempts"]), "result": result})


@app.route("/api/weak-areas")
def weak_areas():
    data = load_data()
    return jsonify(data["weakAreas"])


@app.route("/api/report")
def report():
    data = load_data()
    return jsonify({
        "profile": data["profile"],
        "practiceAttempts": len(data["practiceAttempts"]),
        "savedAnswers": len(data["answers"]),
        "mockAttemptCount": len(data["mockAttempts"]),
        "mockAttempts": data["mockAttempts"],
        "weakAreas": data["weakAreas"],
        "uploadedDocuments": data["uploadedDocuments"],
        "readingPositionsCount": len(data["readingProgress"]),
        "bookmarkCount": len(data["bookmarks"]),
    })


@app.route("/api/upload", methods=["POST"])
def upload():
    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"error": "No file supplied"}), 400

    filename = secure_filename(file.filename)
    suffix = Path(filename).suffix.lower()
    if suffix not in {".pdf", ".doc", ".docx"}:
        return jsonify({"error": "Only PDF, DOC and DOCX files are supported"}), 400

    upload_dir = current_upload_dir()
    upload_dir.mkdir(parents=True, exist_ok=True)
    requested_path = upload_dir / filename
    if requested_path.exists():
        stem = Path(filename).stem
        counter = 2
        while (upload_dir / f"{stem} ({counter}){suffix}").exists():
            counter += 1
        filename = f"{stem} ({counter}){suffix}"
    saved_path = upload_dir / filename
    file.save(saved_path)
    text = ""

    try:
        if suffix == ".pdf":
            reader = PdfReader(str(saved_path))
            text = "\n".join((page.extract_text() or "") for page in reader.pages)
        elif suffix == ".docx":
            document = Document(str(saved_path))
            text = "\n".join(paragraph.text for paragraph in document.paragraphs)
        else:
            text = ""
    except Exception as exc:
        saved_path.unlink(missing_ok=True)
        return jsonify({"error": "Document processing failed", "detail": str(exc)}), 422

    if text:
        text_path = saved_path.with_suffix(".txt")
        text_path.write_text(text, encoding="utf-8")
    data = load_data()
    record = {"name": filename, "size": saved_path.stat().st_size, "characters": len(text),
              "status": "processed" if text else "stored; legacy DOC extraction unavailable"}
    data["uploadedDocuments"].append(record)
    save_data(data)
    return jsonify({"status": record["status"], "name": filename, "characters": len(text), "preview": text[:500]})


if __name__ == "__main__":
    app.run(
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "4173")),
        debug=False,
    )

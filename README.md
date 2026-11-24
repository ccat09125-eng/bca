# BCA Study & Exam Hub

A responsive, source-backed study and examination portal for the supplied University of Madras BCA materials.

## Run locally

From this directory in PowerShell (Python dependencies are listed in `requirements.txt`):

```powershell
python -m pip install -r requirements.txt
python server.py
```

Open <http://127.0.0.1:4173/>. Student data and uploads are stored locally in this app directory.

## Render deployment

`render.yaml`, `.python-version` and `requirements-prod.txt` configure a Render web service. Connect this repository in the Render dashboard and use the included Blueprint. No public deployment has been created yet.

The free Blueprint uses an ephemeral filesystem: anonymous browser sessions are isolated, but profiles, uploads and progress can be lost when the service restarts or redeploys. Persistent Render disks require a paid web service. This MVP has no account login; do not use it to store sensitive personal information.

## Student features

- Landing page, student onboarding and editable semester/exam profile
- Dashboard, semester-specific subjects, unit navigation and study progress
- Reader for all three supplied DOCX notebooks, with paragraph/table-row source locations, subject filters, bookmarks and saved positions
- Global search across extracted notebook text and the current question-level PYQ bank
- Course-material library, plus PDF/DOC/DOCX uploads
- Actual PYQ question bank with source-paper references and links
- Supplied model Q&A practice, answer writing, rule-based feedback and saved attempts
- Flashcards, weekly planner and weak-topic recommendations
- Timed university-pattern mock exam with autosave/resume, submission and submitted-answer results
- Direct URLs for dashboard, semesters, subjects, notes, library, PYQs, questions, practice, flashcards, exams, planner, progress and search

## Data and processing

- `academic_documents/` contains copies of the three tagged source DOCX files; the supplied originals are not modified.
- `process_academic_docs.py` regenerates `academic_content.json` and `academic_processing_report.json` from those source files.
- The reader retains all non-empty paragraphs and table rows and uses paragraph/table-row references. Printed page numbers are unavailable in these DOCX files.
- Subject/semester mapping uses explicit section headings; unverified references are not treated as authoritative coverage.
- In local mode, `bca_data.json` stores the student profile, exam drafts, attempts, answers, weak areas, reading positions, bookmarks and upload metadata. It is intentionally excluded from Git.
- In public mode (`PUBLIC_DEPLOY=true`), anonymous browser sessions are stored separately under `DATA_DIR`; a configured `APP_SECRET_KEY` is required.
- `uploads/` stores uploaded documents and extracted PDF/DOCX text.
- Keep the sibling `academic_inventory/` folder available; it contains course-book text and indexed paper sources used by readers and source links.
- The current question bank contains 120 actual questions from five cited papers. The wider inventory has 103 indexed PDF files, but the remaining files have not been converted into question-level bank records.
- 144 supplied model Q&A records are available for answer guidance; they are not additional verified PYQs.
- PDF and DOCX uploads are text-extracted. Legacy DOC is stored but cannot currently be text-extracted.

## Limitations

There is no configured AI API: answer feedback and mock marks are heuristic practice estimates, not official marking. Persistence is local JSON/filesystem storage for a single-user MVP; authentication, multi-user isolation, cloud database and production deployment are not configured.

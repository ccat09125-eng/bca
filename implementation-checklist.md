# BCA Study & Exam Hub — implementation status

## Working MVP

- [x] Responsive landing page and student onboarding
- [x] Saved student profile, semester selection and dashboard
- [x] Subject/unit navigation for semesters I–III
- [x] Three supplied DOCX notebooks extracted and readable in the app
- [x] Notebook reader has subject filters, source locations, saved reading positions and bookmarks
- [x] Search across extracted source blocks and available PYQs
- [x] PDF, DOC and DOCX uploads; PDF/DOCX text extraction
- [x] 120 question-level PYQs from five cited papers, with source links
- [x] 144 supplied model Q&A records, answer writing and non-AI feedback
- [x] Flashcards, study planner, progress/weak-area dashboard
- [x] Timed mock exam with autosave/resume, submission and answer-by-answer estimated results
- [x] Local JSON/filesystem persistence and direct URLs for main pages
- [x] Render Blueprint and production Gunicorn requirements prepared
- [x] Public-mode data and upload paths isolated per anonymous browser session
- [x] Local state, upload and data directories excluded from Git

## Known gaps / next priorities

- [ ] Convert the remaining indexed PYQ PDFs into verified question-level records in resumable batches; do not treat PDF indexing as question extraction
- [ ] Convert legacy DOC files before text extraction
- [ ] Add AI feedback only after a provider/API key is configured; current answer guidance and marks are heuristic
- [ ] Configure authentication, multi-user database/storage, production hosting and deployment
- [ ] Connect and push to the specified GitHub repository; exact owner/repository URL is still required
- [ ] Create the Render service after repository connection; free-tier persistence is ephemeral
- [ ] Printed page numbers are unavailable in the supplied DOCX files; citations use paragraph/table-row locations

## Validation

- [x] Python syntax check for the server and extraction script
- [x] JavaScript syntax check for the browser app
- [x] Flask API checks for source listing/reading, search, PYQ count, reading-state persistence and bookmark create/delete
- [x] Browser checks for landing, onboarding screen, source reader, notebook search, Q&A list and answer-practice navigation

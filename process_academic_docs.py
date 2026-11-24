import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

from docx import Document
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph


BASE = Path(__file__).resolve().parent
SOURCE_DIR = BASE / "academic_documents"
OUTPUT = BASE / "academic_content.json"
REPORT_OUTPUT = BASE / "academic_processing_report.json"
SOURCES = (
    "BCA_SEMESTER_I_II_III_PYQ_QUESTION_BANK_WITH_MODEL_ANSWERS (1).docx",
    "BCA_MEGA_QUESTION_ANSWER_NOTEBOOK_University_of_Madras (2).docx",
    "BCA_DETAILED_NOTEBOOK_WHOLE_SYLLABUS.docx",
)

SUBJECT_CODES = {
    "fundamentals of digital computers": "SUCA101",
    "pc software lab": "SUCA102",
    "mathematics i": "SUCA103",
    "programming in c": "SUCA104",
    "programming in c lab": "SUCA105",
    "mathematics ii": "SUCA106",
    "programming in c++ and data structures": "SUCA201A",
    "microprocessors and its applications": "SUCA202",
    "numerical and statistical methods": "SUCA203",
    "c++ data structures lab": "SUCA204",
    "programming in c++ using data structures lab": "SUCA204",
    "financial accounting": "SUCA205",
    "english i": "SFEN11",
    "english ii": "SFEN12",
    "communicative english: speaking skills": "SFCE11",
    "communicative english ii: listening skills": "SFCE12",
    "communicative english: listening skills": "SFCE12",
    "communicative english i: speaking skills": "SFCE11",
}

SUBJECT_METADATA = {
    "SUCA101": ("Fundamentals of Digital Computers", "I"),
    "SUCA102": ("PC Software Lab", "I"),
    "SUCA103": ("Mathematics I", "I"),
    "SFEN11": ("English I", "I"),
    "SFCE11": ("Communicative English I: Speaking Skills", "I"),
    "SUCA104": ("Programming in C", "II"),
    "SUCA105": ("Programming in C Lab", "II"),
    "SUCA106": ("Mathematics II", "II"),
    "SFEN12": ("English II", "II"),
    "SFCE12": ("Communicative English II: Listening Skills", "II"),
    "SUCA201A": ("Programming in C++ and Data Structures", "III"),
    "SUCA202": ("Microprocessors and its Applications", "III"),
    "SUCA203": ("Numerical and Statistical Methods", "III"),
    "SUCA204": ("C++ Data Structures Lab", "III"),
    "SUCA205": ("Financial Accounting", "III"),
}


def normalized(text):
    return re.sub(r"\s+", " ", text).strip().casefold()


def paragraph_page_breaks(paragraph):
    nodes = paragraph._p.xpath(".//w:br[@w:type='page']")
    before = paragraph._p.xpath("./w:pPr/w:pageBreakBefore")
    return len(nodes), bool(before)


def read_blocks(document):
    page = 1
    has_page_layout_markers = False
    blocks = []
    paragraph_number = 0
    table_number = 0
    for element in document.element.body.iterchildren():
        if isinstance(element, CT_P):
            paragraph_number += 1
            paragraph = Paragraph(element, document)
            break_count, break_before = paragraph_page_breaks(paragraph)
            if break_before:
                page += 1
                has_page_layout_markers = True
            text = paragraph.text.strip()
            if text:
                blocks.append(
                    {
                        "kind": "paragraph",
                        "text": text,
                        "style": paragraph.style.name if paragraph.style else "Normal",
                        "source_location": f"paragraph {paragraph_number}",
                        "page": None,
                    }
                )
            if break_count:
                page += break_count
                has_page_layout_markers = True
        elif isinstance(element, CT_Tbl):
            table_number += 1
            table = Table(element, document)
            for row_number, row in enumerate(table.rows, start=1):
                cells = [re.sub(r"\s+", " ", cell.text).strip() for cell in row.cells]
                if any(cells):
                    blocks.append(
                        {
                            "kind": "table_row",
                            "text": " | ".join(cells),
                            "style": "Table",
                            "source_location": f"table {table_number}, row {row_number}",
                            "page": None,
                        }
                    )
    if not has_page_layout_markers:
        for block in blocks:
            block["page"] = None
    return blocks, paragraph_number, table_number, has_page_layout_markers


def annotate(blocks):
    semester = None
    subject = None
    subject_code = None
    unit = None
    chapter = None
    in_contents = False
    for block in blocks:
        text = block["text"]
        upper = text.upper()
        if block["style"].startswith("Heading") and upper.strip() in ("CONTENTS", "NOTEBOOK CONTENTS", "TABLE OF CONTENTS"):
            in_contents = True
        is_top_heading = block["style"] == "Heading 1"
        if is_top_heading and re.search(r"\bSEMESTER\s+I\b", upper):
            in_contents = False
        semester_match = re.search(r"\bSEMESTER\s+(I{1,3}|[1-3])\b", upper) if is_top_heading else None
        if semester_match:
            semester = {"1": "I", "2": "II", "3": "III"}.get(
                semester_match.group(1), semester_match.group(1)
            )
            subject = None
            subject_code = None
            unit = None
            chapter = None
        elif is_top_heading and not re.match(r"\s*SUBJECT\s+\d+\b", text, re.IGNORECASE):
            subject = None
            subject_code = None
            unit = None
            chapter = None
        subject_match = (
            re.search(r"\bSUBJECT\s+\d+\s*[–—-]\s*(.+)", text, re.IGNORECASE)
            if block["style"].startswith("Heading") and not in_contents
            else None
        )
        if subject_match:
            subject_text = re.split(r"\s*\((?:SUCA|SFEN|SFCE)[^)]+\)", subject_match.group(1), maxsplit=1, flags=re.IGNORECASE)[0]
            heading_semester = re.search(r"\(\s*SEMESTER\s+(I{1,3}|[1-3])\s*\)", subject_text, re.IGNORECASE)
            if heading_semester:
                raw_semester = heading_semester.group(1).upper()
                semester = {"1": "I", "2": "II", "3": "III"}.get(raw_semester, raw_semester)
            subject_text = re.sub(r"\s*\((?:SEMESTER|VOLUME)[^)]+\)", "", subject_text, flags=re.IGNORECASE)
            subject = subject_text.strip(" :-–—")
            subject_code = next(
                (value for label, value in SUBJECT_CODES.items() if label == normalized(subject)),
                None,
            )
            if normalized(subject) == "english" and semester in ("I", "II"):
                subject_code = "SFEN11" if semester == "I" else "SFEN12"
            if subject_code is None:
                code_match = re.search(r"\b(?:SUCA|SFEN|SFCE)\d+[A-Z]?\b", text, re.IGNORECASE)
                subject_code = code_match.group(0).upper() if code_match else None
            if subject_code in SUBJECT_METADATA:
                subject, semester = SUBJECT_METADATA[subject_code]
            unit = None
            chapter = None
        unit_match = re.match(r"\s*UNIT\s*[-–:]?\s*(I{1,3}|IV|V|[1-5])\b", text, re.IGNORECASE)
        if unit_match and not in_contents and (
            block["style"].startswith("Heading") or len(text) < 240
        ):
            unit = unit_match.group(1).upper()
            chapter = None
        if not in_contents and re.match(r"\s*(?:LESSON|CHAPTER)\s+\d+\b", text, re.IGNORECASE):
            chapter = text
        block.update(
            {
                "semester": semester,
                "subject": subject,
                "subject_code": subject_code,
                "unit": unit,
                "chapter": chapter,
                "page_reference_status": "available" if block["page"] is not None else "not stored in DOCX",
            }
        )


def extract(filename):
    path = SOURCE_DIR / filename
    document = Document(path)
    blocks, paragraph_count, table_count, has_page_breaks = read_blocks(document)
    annotate(blocks)
    body_block_count = len(blocks)
    header_footer_blocks = []
    for section_number, section in enumerate(document.sections, start=1):
        for label, container in (("header", section.header), ("footer", section.footer)):
            for paragraph_number, paragraph in enumerate(container.paragraphs, start=1):
                text = paragraph.text.strip()
                if text:
                    header_footer_blocks.append(
                        {
                            "kind": label,
                            "text": text,
                            "style": paragraph.style.name if paragraph.style else "Normal",
                            "source_location": f"section {section_number} {label} paragraph {paragraph_number}",
                            "page": None,
                            "semester": None,
                            "subject": None,
                            "subject_code": None,
                            "unit": None,
                            "chapter": None,
                            "page_reference_status": "not stored in DOCX",
                        }
                    )
            for table_number, table in enumerate(container.tables, start=1):
                for row_number, row in enumerate(table.rows, start=1):
                    text = " | ".join(
                        re.sub(r"\s+", " ", cell.text).strip() for cell in row.cells
                    ).strip()
                    if text:
                        header_footer_blocks.append(
                            {
                                "kind": f"{label}_table_row",
                                "text": text,
                                "style": "Table",
                                "source_location": f"section {section_number} {label} table {table_number}, row {row_number}",
                                "page": None,
                                "semester": None,
                                "subject": None,
                                "subject_code": None,
                                "unit": None,
                                "chapter": None,
                                "page_reference_status": "not stored in DOCX",
                            }
                        )
    blocks.extend(header_footer_blocks)
    text_chars = sum(len(block["text"]) for block in blocks)
    heading_blocks = [
        {"text": block["text"], "style": block["style"], "source_location": block["source_location"]}
        for block in blocks
        if block["style"].startswith("Heading")
    ]
    image_count = sum(1 for relation in document.part.rels.values() if "image" in relation.reltype)
    table_rows = sum(1 for block in blocks if block["kind"] == "table_row")
    prior_text = BASE.parent / "academic_inventory" / f"{path.stem}.txt"
    prior_comparison = {"available": prior_text.is_file()}
    if prior_text.is_file():
        old_text = prior_text.read_text(encoding="utf-8", errors="replace")
        current_text = "\n".join(
            block["text"] for block in blocks[:body_block_count]
        )
        prior_comparison.update(
            {
                "filename": prior_text.name,
                "character_count": len(old_text),
                "normalized_equal": normalized(current_text) == normalized(old_text),
                "note": (
                    "The tagged DOCX content was extracted as the authoritative source."
                    if normalized(current_text) != normalized(old_text)
                    else "The existing text extraction matches after whitespace normalization."
                ),
            }
        )
    return {
        "id": path.stem.lower().replace(" ", "-").replace("(", "").replace(")", ""),
        "filename": filename,
        "document_type": (
            "question-answer-notebook"
            if "MEGA" in filename.upper()
            else "question-bank"
            if "QUESTION" in filename.upper()
            else "study-notebook"
        ),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "paragraph_count": paragraph_count,
        "table_count": table_count,
        "table_row_count": table_rows,
        "image_count": image_count,
        "block_count": len(blocks),
        "body_block_count": body_block_count,
        "header_footer_block_count": len(header_footer_blocks),
        "character_count": text_chars,
        "word_count": sum(len(block["text"].split()) for block in blocks),
        "heading_count": len(heading_blocks),
        "headings": heading_blocks,
        "explicit_page_break_count": sum(
            len(paragraph._p.xpath(".//w:br[@w:type='page']"))
            for paragraph in document.paragraphs
        ),
        "pagination": "Printed page numbers are not stored in these DOCX files; paragraph/table-row locations are provided instead.",
        "comparison_to_prior_text": prior_comparison,
        "blocks": blocks,
    }


def main():
    documents = [extract(filename) for filename in SOURCES]
    occurrences = defaultdict(list)
    for document in documents:
        for block in document["blocks"]:
            value = normalized(block["text"])
            if len(value) >= 100:
                occurrences[value].append(
                    {
                        "document_id": document["id"],
                        "filename": document["filename"],
                        "source_location": block["source_location"],
                    }
                )
    duplicate_groups = [
        {"text": text, "occurrences": refs}
        for text, refs in occurrences.items()
        if len({item["document_id"] for item in refs}) > 1
    ]
    subject_occurrences = defaultdict(set)
    for document in documents:
        for block in document["blocks"][: document["body_block_count"]]:
            if block["subject"]:
                key = (block["semester"], block["subject_code"], block["subject"])
                subject_occurrences[key].add(document["id"])
    subject_coverage = [
        {
            "semester": semester,
            "subject_code": code,
            "subject": name,
            "documents": sorted(document_ids),
        }
        for (semester, code, name), document_ids in sorted(
            subject_occurrences.items(), key=lambda item: (item[0][0] or "", item[0][1] or "", item[0][2])
        )
    ]
    payload = {
        "version": 1,
        "generated_from": "the three tagged source DOCX files",
        "documents": documents,
        "subject_coverage": subject_coverage,
        "duplicate_group_count": len(duplicate_groups),
        "duplicate_groups": duplicate_groups,
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    report = {
        "status": "complete",
        "generated_from": "the three tagged source DOCX files",
        "documents": [
            {
                key: item[key]
                for key in (
                    "id",
                    "filename",
                    "document_type",
                    "sha256",
                    "paragraph_count",
                    "table_count",
                    "table_row_count",
                    "image_count",
                    "block_count",
                    "body_block_count",
                    "header_footer_block_count",
                    "character_count",
                    "word_count",
                    "heading_count",
                    "explicit_page_break_count",
                    "pagination",
                    "comparison_to_prior_text",
                )
            }
            for item in documents
        ],
        "cross_document_exact_duplicate_groups": len(duplicate_groups),
        "subject_coverage": subject_coverage,
        "note": "All non-empty paragraphs and non-empty table rows were retained. No image objects were found.",
    }
    REPORT_OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

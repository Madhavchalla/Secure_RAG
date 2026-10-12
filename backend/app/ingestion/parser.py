import os
from typing import List, Dict, Any
import pymupdf  # PyMuPDF
import docx


class DocumentParser:
    """
    Multi-format document text extraction engine.
    Extracts text while preserving page numbers and section metadata.
    """

    @staticmethod
    def parse_pdf(file_path: str) -> List[Dict[str, Any]]:
        """
        Extract text page by page from PDF files using PyMuPDF.
        """
        pages = []
        with pymupdf.open(file_path) as doc:
            for page_idx, page in enumerate(doc):
                text = page.get_text()
                if text and text.strip():
                    pages.append({
                        "page_number": page_idx + 1,
                        "text": text.strip(),
                    })
        return pages

    @staticmethod
    def parse_docx(file_path: str) -> List[Dict[str, Any]]:
        """
        Extract text from Microsoft Word documents.
        Simulates page/section increments based on paragraph groupings.
        """
        doc = docx.Document(file_path)
        pages = []
        current_page_text = []
        current_page_num = 1
        word_count = 0

        for paragraph in doc.paragraphs:
            text = paragraph.text.strip()
            if text:
                current_page_text.append(text)
                word_count += len(text.split())
                # Roughly 400 words per logical page in DOCX
                if word_count > 400:
                    pages.append({
                        "page_number": current_page_num,
                        "text": "\n".join(current_page_text),
                    })
                    current_page_text = []
                    current_page_num += 1
                    word_count = 0

        if current_page_text:
            pages.append({
                "page_number": current_page_num,
                "text": "\n".join(current_page_text),
            })

        return pages

    @staticmethod
    def parse_text(file_path: str) -> List[Dict[str, Any]]:
        """
        Extract text from plain text or markdown files.
        """
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        # Split into logical sections if delimiter exists, otherwise single page
        sections = content.split("================================================================================")
        pages = []
        page_num = 1
        for sec in sections:
            clean = sec.strip()
            if clean:
                pages.append({
                    "page_number": page_num,
                    "text": clean,
                })
                page_num += 1

        if not pages and content.strip():
            pages.append({
                "page_number": 1,
                "text": content.strip(),
            })

        return pages

    @classmethod
    def extract_document(cls, file_path: str, filename: str) -> List[Dict[str, Any]]:
        """
        Dispatch extraction based on file extension.
        """
        ext = os.path.splitext(filename)[1].lower()
        if ext == ".pdf":
            return cls.parse_pdf(file_path)
        elif ext in [".docx", ".doc"]:
            return cls.parse_docx(file_path)
        elif ext in [".txt", ".md"]:
            return cls.parse_text(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}. Allowed: .pdf, .docx, .txt, .md")

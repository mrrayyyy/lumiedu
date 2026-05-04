from __future__ import annotations

import logging
import re

from config import settings

logger = logging.getLogger("knowledge.chunker")


class TextChunker:
    @staticmethod
    def extract_text(content: bytes, filename: str) -> str:
        lower = filename.lower()
        if lower.endswith(".txt") or lower.endswith(".md"):
            return content.decode("utf-8", errors="replace")
        if lower.endswith(".pdf"):
            return TextChunker._extract_pdf(content)
        if lower.endswith(".docx"):
            return TextChunker._extract_docx(content)
        return content.decode("utf-8", errors="replace")

    @staticmethod
    def chunk_text(text: str) -> list[str]:
        max_size = settings.max_chunk_size
        overlap = settings.chunk_overlap

        paragraphs = re.split(r"\n\s*\n", text.strip())
        chunks: list[str] = []
        current = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if len(current) + len(para) + 2 <= max_size:
                current = f"{current}\n\n{para}".strip() if current else para
            else:
                if current:
                    chunks.append(current)
                if len(para) > max_size:
                    words = para.split()
                    current = ""
                    for word in words:
                        if len(current) + len(word) + 1 <= max_size:
                            current = f"{current} {word}".strip() if current else word
                        else:
                            if current:
                                chunks.append(current)
                            current = word
                else:
                    if chunks and overlap > 0:
                        prev_tail = chunks[-1][-overlap:]
                        current = f"{prev_tail} {para}".strip()
                    else:
                        current = para

        if current:
            chunks.append(current)

        return chunks

    @staticmethod
    def _extract_pdf(content: bytes) -> str:
        try:
            import io
            import PyPDF2
            reader = PyPDF2.PdfReader(io.BytesIO(content))
            parts = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    parts.append(text)
            return "\n\n".join(parts)
        except Exception as exc:
            logger.warning("PDF extraction failed: %s", exc)
            return ""

    @staticmethod
    def _extract_docx(content: bytes) -> str:
        try:
            import io
            import docx
            doc = docx.Document(io.BytesIO(content))
            parts = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    parts.append(paragraph.text)
            return "\n\n".join(parts)
        except Exception as exc:
            logger.warning("DOCX extraction failed: %s", exc)
            return ""

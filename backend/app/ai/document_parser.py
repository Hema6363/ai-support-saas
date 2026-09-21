import os
import re
import logging
from typing import List, Dict, Any, Tuple, Optional
from pypdf import PdfReader
import docx

logger = logging.getLogger(__name__)


class DocumentParser:
    def __init__(self, chunk_size: int = 700, chunk_overlap: int = 120):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def extract_text(self, file_path: str, file_type: str) -> str:
        """Extract plain text from various file formats."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found at {file_path}")

        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == ".pdf" or "pdf" in file_type:
            return self._extract_pdf(file_path)
        elif ext in [".docx", ".doc"] or "word" in file_type or "officedocument" in file_type:
            return self._extract_docx(file_path)
        else:
            return self._extract_text_file(file_path)

    def _extract_pdf(self, file_path: str) -> str:
        reader = PdfReader(file_path)
        pages_text = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                pages_text.append(text)
        return "\n\n".join(pages_text)

    def _extract_docx(self, file_path: str) -> str:
        doc = docx.Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n\n".join(paragraphs)

    def _extract_text_file(self, file_path: str) -> str:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            with open(file_path, "r", encoding="latin-1", errors="ignore") as f:
                return f.read()

    def clean_text(self, text: str) -> str:
        """Clean and normalize raw extracted text."""
        text = re.sub(r"\r\n|\r", "\n", text)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def split_into_chunks(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Split text into semantic overlapping chunks."""
        cleaned = self.clean_text(text)
        if not cleaned:
            return []

        chunks: List[str] = []
        paragraphs = cleaned.split("\n\n")
        current_chunk = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if len(para) > self.chunk_size:
                sentences = re.split(r"(?<=[.!?])\s+", para)
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                    if len(current_chunk) + len(sentence) + 1 <= self.chunk_size:
                        current_chunk = f"{current_chunk} {sentence}".strip()
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                        if len(sentence) > self.chunk_size:
                            for i in range(0, len(sentence), self.chunk_size - self.chunk_overlap):
                                chunks.append(sentence[i : i + self.chunk_size])
                            current_chunk = ""
                        else:
                            current_chunk = sentence
            else:
                if len(current_chunk) + len(para) + 2 <= self.chunk_size:
                    if current_chunk:
                        current_chunk = f"{current_chunk}\n\n{para}"
                    else:
                        current_chunk = para
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = para

        if current_chunk:
            chunks.append(current_chunk)

        result_chunks = []
        for idx, chunk_text in enumerate(chunks):
            chunk_data = {
                "chunk_index": idx,
                "text": chunk_text,
                "char_count": len(chunk_text),
            }
            if metadata:
                chunk_data["metadata"] = metadata
            result_chunks.append(chunk_data)

        return result_chunks


document_parser = DocumentParser()

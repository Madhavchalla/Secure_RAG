from typing import List, Dict, Any


class TextChunker:
    """
    Recursive character text splitter that preserves page numbering and document hierarchy.
    """

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_pages(self, pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Split a list of page objects into manageable chunks with overlap,
        ensuring chunk-to-page mappings remain accurate.
        """
        chunks = []
        global_chunk_index = 0

        for page in pages:
            page_num = page["page_number"]
            text = page["text"].strip()
            if not text:
                continue

            # If the entire page fits in one chunk
            if len(text) <= self.chunk_size:
                chunks.append({
                    "chunk_index": global_chunk_index,
                    "page_number": page_num,
                    "content": text,
                    "content_preview": text[:120].replace("\n", " "),
                })
                global_chunk_index += 1
                continue

            # Otherwise, split by paragraphs or sliding window
            paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
            current_chunk = ""

            for p in paragraphs:
                if len(current_chunk) + len(p) + 1 <= self.chunk_size:
                    current_chunk = f"{current_chunk}\n{p}".strip()
                else:
                    if current_chunk:
                        chunks.append({
                            "chunk_index": global_chunk_index,
                            "page_number": page_num,
                            "content": current_chunk,
                            "content_preview": current_chunk[:120].replace("\n", " "),
                        })
                        global_chunk_index += 1
                    
                    # If single paragraph exceeds chunk size, slice with overlap
                    if len(p) > self.chunk_size:
                        start = 0
                        while start < len(p):
                            end = start + self.chunk_size
                            sub = p[start:end]
                            chunks.append({
                                "chunk_index": global_chunk_index,
                                "page_number": page_num,
                                "content": sub,
                                "content_preview": sub[:120].replace("\n", " "),
                            })
                            global_chunk_index += 1
                            start += (self.chunk_size - self.chunk_overlap)
                        current_chunk = ""
                    else:
                        current_chunk = p

            if current_chunk:
                chunks.append({
                    "chunk_index": global_chunk_index,
                    "page_number": page_num,
                    "content": current_chunk,
                    "content_preview": current_chunk[:120].replace("\n", " "),
                })
                global_chunk_index += 1

        return chunks


# Singleton chunker instance
text_chunker = TextChunker(chunk_size=500, chunk_overlap=50)

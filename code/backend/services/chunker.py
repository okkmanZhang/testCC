import re
from typing import List, Dict, Tuple, Optional
from services.pdf_parser import detect_section


def chunk_pages(pages: List[Dict], max_chars: int = 800, overlap_chars: int = 100) -> List[Dict]:
    """Merge all pages then split on Award clause boundaries."""
    full_text = ""
    page_map = []

    for page in pages:
        start = len(full_text)
        full_text += page["text"] + "\n\n"
        page_map.append((start, page["page_num"]))

    boundary_pattern = re.compile(
        r'\n(?=(?:\d+\.\d+\s)|(?:Schedule\s+[A-Z])|(?:Appendix\s+[A-Z])|(?:PART\s+\d+))',
        re.IGNORECASE
    )
    raw_splits = boundary_pattern.split(full_text)

    chunks = []
    for split in raw_splits:
        split = split.strip()
        if len(split) < 50:
            continue

        sub_chunks = _split_long_chunk(split, max_chars, overlap_chars) if len(split) > max_chars else [split]

        for chunk_text in sub_chunks:
            section, clause = detect_section(chunk_text)
            page_num = _find_page(chunk_text, full_text, page_map)
            chunks.append({
                "chunk_text": chunk_text,
                "section": section,
                "clause": clause,
                "page_num": page_num,
            })

    print(f"Created {len(chunks)} chunks")
    return chunks


def _split_long_chunk(text: str, max_chars: int, overlap: int) -> List[str]:
    """Split oversized chunks at sentence boundaries with overlap."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    result, current = [], ""
    for sent in sentences:
        if len(current) + len(sent) > max_chars and current:
            result.append(current.strip())
            current = current[-overlap:] + " " + sent
        else:
            current += " " + sent
    if current.strip():
        result.append(current.strip())
    return result


def _find_page(chunk_text: str, full_text: str, page_map: List[tuple]) -> Optional[int]:
    """Find which page a chunk originated from."""
    pos = full_text.find(chunk_text[:50])
    if pos == -1:
        return None
    for i in range(len(page_map) - 1, -1, -1):
        if page_map[i][0] <= pos:
            return page_map[i][1]
    return None
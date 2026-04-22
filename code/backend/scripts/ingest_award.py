import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from services.pdf_parser import parse_pdf
from services.chunker import chunk_pages
from services.embedder import embed_and_store


def main():
    pdf_path = os.getenv("AWARD_PDF_PATH")
    if not pdf_path or not os.path.exists(pdf_path):
        print(f"PDF not found at: {pdf_path}")
        sys.exit(1)

    print(f"Parsing PDF: {pdf_path}")
    pages = parse_pdf(pdf_path)

    print("Chunking...")
    chunks = chunk_pages(pages)

    print(f"Embedding and storing {len(chunks)} chunks...")
    stored = embed_and_store(chunks)

    print(f"\nDone! Stored {stored} chunks into award_chunks table")


if __name__ == "__main__":
    main()
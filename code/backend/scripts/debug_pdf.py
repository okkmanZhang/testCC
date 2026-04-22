# scripts/debug_pdf.py
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()
from services.pdf_parser import parse_pdf

pages = parse_pdf(os.getenv("AWARD_PDF_PATH"))
# Print first 3 pages raw text
for p in pages[:3]:
    print(f"\n--- PAGE {p['page_num']} ---")
    print(p["text"][:500])
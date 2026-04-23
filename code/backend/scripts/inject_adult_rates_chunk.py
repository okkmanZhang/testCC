import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from openai import AzureOpenAI
from sqlalchemy import text
from models.database import SessionLocal

AWARD_ID = "MA000004"

# Clean synthetic chunk — adult minimum rates Table 4 (effective 01 Jul 2025)
ADULT_RATES_CHUNK = """clause 17.1 Adult rates — Table 4 Minimum rates (effective 1 July 2025)
General Retail Industry Award 2020 [MA000004]

Classification               | Weekly rate | Hourly rate
Retail Employee Level 1      | $1,010.20   | $26.59
Retail Employee Level 2      | $1,033.40   | $27.20
Retail Employee Level 3      | $1,048.60   | $27.60
Retail Employee Level 4      | $1,069.90   | $28.15
Retail Employee Level 5      | $1,100.50   | $28.96
Retail Employee Level 6      | $1,151.40   | $30.30
Retail Employee Level 7      | $1,229.70   | $32.36
Retail Employee Level 8      | $1,297.70   | $34.15

These are the minimum adult rates (age 21+) for full-time and part-time employees.
Junior rates (under 21) are a percentage of these rates per clause 17.2 Table 5.
Casual employees receive a 25% loading on top of these rates per clause 13.2.
Reference: clause 17.1, Table 4, MA000004.
"""


def inject():
    client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
    )
    embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME")

    resp = client.embeddings.create(model=embedding_deployment, input=ADULT_RATES_CHUNK)
    embedding_str = "[" + ",".join(str(x) for x in resp.data[0].embedding) + "]"

    db = SessionLocal()
    try:
        # Remove any previous synthetic adult rate chunk
        db.execute(text("""
            DELETE FROM award_chunks
            WHERE award_id = :award_id AND clause = '17.1-synthetic'
        """), {"award_id": AWARD_ID})

        db.execute(text("""
            INSERT INTO award_chunks
                (award_id, chunk_text, embedding, section, clause, page_num, metadata)
            VALUES
                (:award_id, :chunk_text, CAST(:embedding AS vector),
                 :section, :clause, :page_num, CAST(:metadata AS jsonb))
        """), {
            "award_id": AWARD_ID,
            "chunk_text": ADULT_RATES_CHUNK,
            "embedding": embedding_str,
            "section": "Table 4",
            "clause": "17.1-synthetic",
            "page_num": 28,
            "metadata": '{"synthetic": true}'
        })

        db.commit()
        print("Injected adult rates synthetic chunk (clause 17.1-synthetic)")
    finally:
        db.close()


OVERTIME_CHUNK = """clause 26 Overtime — General Retail Industry Award 2020 [MA000004]

Full-time employees:
- Overtime is payable for all hours worked in excess of 38 ordinary hours per week (clause 26.1)
- Or in excess of the agreed daily hours under the employee's roster
- Overtime rate: 150% for first 3 hours, 200% thereafter (Table 11)
- Double time on Sundays and public holidays

Part-time employees:
- Overtime payable for hours worked beyond guaranteed hours agreed under clause 10.5 (clause 10.8)
- Guaranteed hours cannot result in 38 or more ordinary hours per week (clause 10.6)

Casual employees:
- Overtime payable for hours worked in excess of 38 ordinary hours per week (clause 26.2)

Reference: clause 26, clause 10.8, Table 11, MA000004.
"""


def inject_overtime():
    client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
    )
    embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME")

    resp = client.embeddings.create(model=embedding_deployment, input=OVERTIME_CHUNK)
    embedding_str = "[" + ",".join(str(x) for x in resp.data[0].embedding) + "]"

    db = SessionLocal()
    try:
        db.execute(text("""
            DELETE FROM award_chunks
            WHERE award_id = :award_id AND clause = '26-synthetic'
        """), {"award_id": AWARD_ID})

        db.execute(text("""
            INSERT INTO award_chunks
                (award_id, chunk_text, embedding, section, clause, page_num, metadata)
            VALUES
                (:award_id, :chunk_text, CAST(:embedding AS vector),
                 :section, :clause, :page_num, CAST(:metadata AS jsonb))
        """), {
            "award_id": AWARD_ID,
            "chunk_text": OVERTIME_CHUNK,
            "embedding": embedding_str,
            "section": "Overtime",
            "clause": "26-synthetic",
            "page_num": 43,
            "metadata": '{"synthetic": true}'
        })

        db.commit()
        print("Injected overtime synthetic chunk (clause 26-synthetic)")
    finally:
        db.close()

PUBLIC_HOLIDAY_CHUNK = """clause 28 Public holidays — General Retail Industry Award 2020 [MA000004]

clause 28.1 — Entitlement to public holiday pay (part-time and full-time):
A full-time or part-time employee who is absent on a public holiday that falls on 
a day they would ordinarily work is ENTITLED TO BE PAID for that day at their 
ordinary rate of pay, even if they do not work.

This applies to:
- Full-time employees: entitled to payment for all public holidays
- Part-time employees: entitled to payment if the public holiday falls on a day 
  they are rostered to work (i.e. it is one of their ordinary working days)
- Casual employees: NOT entitled to payment for public holidays not worked

clause 28.2 — Working on a public holiday:
An employee who works on a public holiday is paid at 225% of their ordinary rate.

clause 28.3 — Substitution:
By agreement, a public holiday may be substituted for another day.

Reference: clause 28.1, clause 28.2, National Employment Standards (NES) s.116, MA000004.
"""


def inject_public_holiday():
    client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
    )
    embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME")

    resp = client.embeddings.create(model=embedding_deployment, input=PUBLIC_HOLIDAY_CHUNK)
    embedding_str = "[" + ",".join(str(x) for x in resp.data[0].embedding) + "]"

    db = SessionLocal()
    try:
        db.execute(text("""
            DELETE FROM award_chunks
            WHERE award_id = :award_id AND clause = '28-synthetic'
        """), {"award_id": AWARD_ID})

        db.execute(text("""
            INSERT INTO award_chunks
                (award_id, chunk_text, embedding, section, clause, page_num, metadata)
            VALUES
                (:award_id, :chunk_text, CAST(:embedding AS vector),
                 :section, :clause, :page_num, CAST(:metadata AS jsonb))
        """), {
            "award_id": AWARD_ID,
            "chunk_text": PUBLIC_HOLIDAY_CHUNK,
            "embedding": embedding_str,
            "section": "Public Holidays",
            "clause": "28-synthetic",
            "page_num": 44,
            "metadata": '{"synthetic": true}'
        })

        db.commit()
        print("Injected public holiday synthetic chunk (clause 28-synthetic)")
    finally:
        db.close()

if __name__ == "__main__":
    inject()
    inject_overtime()
    inject_public_holiday()

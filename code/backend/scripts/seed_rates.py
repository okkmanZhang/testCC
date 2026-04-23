import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import text
from models.database import SessionLocal

AWARD_ID = "MA000004"
EFFECTIVE_DATE = "2024-07-01"  # current rates from MA000004

# Base adult hourly rates by classification (clause 17.1, Table 4)
ADULT_RATES = {
    "level_1": 26.59,
    "level_2": 27.20,
    "level_3": 27.60,
    "level_4": 28.15,
    "level_5": 28.96,
    "level_6": 30.30,
    "level_7": 32.36,
    "level_8": 34.15,
}

# Junior rate percentages by age (clause 17.2, Table 5)
# Only applies to levels 1, 2, 3
JUNIOR_RATES = {
    "under_16": 0.45,
    "16": 0.50,
    "17": 0.60,
    "18": 0.70,
    "19": 0.80,
    "20": 0.90,
}

# Penalty multipliers by day type for full-time and part-time (clause 25)
FT_PT_MULTIPLIERS = {
    "weekday":        1.00,  # ordinary hours Mon-Fri
    "saturday":       1.25,  # clause 25.2
    "sunday":         1.50,  # clause 25.3
    "public_holiday": 2.25,  # clause 25.4
}

# Casual loading is 25% on top of base (clause 13.2)
# Then penalty multipliers apply on top of casual rate
CASUAL_LOADING = 1.25

CASUAL_MULTIPLIERS = {
    "weekday":        1.00,
    "saturday":       1.25,
    "sunday":         1.50,
    "public_holiday": 2.25,
}


def seed():
    db = SessionLocal()
    inserted = 0

    try:
        # Clear existing rates for clean reseed
        db.execute(text("DELETE FROM award_rates WHERE award_id = :award_id"), {"award_id": AWARD_ID})
        db.commit()

        rows = []

        for level, base_rate in ADULT_RATES.items():
            classification = f"retail_employee_{level}"

            # --- FULL-TIME & PART-TIME adult rates ---
            for emp_type in ["full_time", "part_time"]:
                for day_type, multiplier in FT_PT_MULTIPLIERS.items():
                    rows.append({
                        "award_id": AWARD_ID,
                        "classification": classification,
                        "employment_type": emp_type,
                        "age_min": 21,
                        "age_max": None,
                        "day_type": day_type,
                        "rate_per_hour": round(base_rate * multiplier, 4),
                        "rate_multiplier": multiplier,
                        "clause_ref": _clause_ref(day_type, is_casual=False),
                        "effective_date": EFFECTIVE_DATE,
                    })

            # --- CASUAL adult rates ---
            for day_type, multiplier in CASUAL_MULTIPLIERS.items():
                casual_rate = round(base_rate * CASUAL_LOADING * multiplier, 4)
                rows.append({
                    "award_id": AWARD_ID,
                    "classification": classification,
                    "employment_type": "casual",
                    "age_min": 21,
                    "age_max": None,
                    "day_type": day_type,
                    "rate_per_hour": casual_rate,
                    "rate_multiplier": round(CASUAL_LOADING * multiplier, 4),
                    "clause_ref": _clause_ref(day_type, is_casual=True),
                    "effective_date": EFFECTIVE_DATE,
                })

            # --- JUNIOR rates (levels 1, 2, 3 only per clause 17.2) ---
            if level in ("level_1", "level_2", "level_3"):
                for age_key, age_pct in JUNIOR_RATES.items():
                    junior_base = round(base_rate * age_pct, 4)
                    age_min, age_max = _parse_age(age_key)

                    # Junior full-time & part-time
                    for emp_type in ["full_time", "part_time"]:
                        for day_type, multiplier in FT_PT_MULTIPLIERS.items():
                            rows.append({
                                "award_id": AWARD_ID,
                                "classification": classification,
                                "employment_type": emp_type,
                                "age_min": age_min,
                                "age_max": age_max,
                                "day_type": day_type,
                                "rate_per_hour": round(junior_base * multiplier, 4),
                                "rate_multiplier": multiplier,
                                "clause_ref": f"cl.17.2, {_clause_ref(day_type, is_casual=False)}",
                                "effective_date": EFFECTIVE_DATE,
                            })

                    # Junior casual
                    for day_type, multiplier in CASUAL_MULTIPLIERS.items():
                        casual_junior_rate = round(junior_base * CASUAL_LOADING * multiplier, 4)
                        rows.append({
                            "award_id": AWARD_ID,
                            "classification": classification,
                            "employment_type": "casual",
                            "age_min": age_min,
                            "age_max": age_max,
                            "day_type": day_type,
                            "rate_per_hour": casual_junior_rate,
                            "rate_multiplier": round(CASUAL_LOADING * multiplier, 4),
                            "clause_ref": f"cl.17.2, {_clause_ref(day_type, is_casual=True)}",
                            "effective_date": EFFECTIVE_DATE,
                        })

        # Bulk insert
        for row in rows:
            db.execute(text("""
                INSERT INTO award_rates
                    (award_id, classification, employment_type, age_min, age_max,
                     day_type, rate_per_hour, rate_multiplier, clause_ref, effective_date)
                VALUES
                    (:award_id, :classification, :employment_type, :age_min, :age_max,
                     :day_type, :rate_per_hour, :rate_multiplier, :clause_ref, :effective_date)
            """), row)
            inserted += 1

        db.commit()
        print(f"Seeded {inserted} rate rows into award_rates")

    finally:
        db.close()


def _parse_age(age_key: str):
    if age_key == "under_16":
        return 0, 15
    elif age_key == "20":
        return 20, 20
    else:
        age = int(age_key)
        return age, age


def _clause_ref(day_type: str, is_casual: bool) -> str:
    base = {
        "weekday":        "cl.17.1",
        "saturday":       "cl.25.2",
        "sunday":         "cl.25.3",
        "public_holiday": "cl.25.4",
    }[day_type]
    return f"{base}, cl.13.2" if is_casual else base


if __name__ == "__main__":
    seed()
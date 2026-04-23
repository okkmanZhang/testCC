import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date, time, datetime, timedelta
from typing import Optional, Dict
from sqlalchemy import text
from models.database import SessionLocal


AWARD_ID = "MA000004"

# Australian public holidays (national) — update yearly
PUBLIC_HOLIDAYS = {
    date(2025, 1, 1),   # New Year's Day
    date(2025, 1, 27),  # Australia Day
    date(2025, 4, 18),  # Good Friday
    date(2025, 4, 19),  # Easter Saturday
    date(2025, 4, 20),  # Easter Sunday
    date(2025, 4, 21),  # Easter Monday
    date(2025, 4, 25),  # Anzac Day
    date(2025, 6, 9),   # King's Birthday
    date(2025, 12, 25), # Christmas Day
    date(2025, 12, 26), # Boxing Day
    date(2026, 1, 1),
    date(2026, 1, 26),
    date(2026, 4, 3),
    date(2026, 4, 4),
    date(2026, 4, 5),
    date(2026, 4, 6),
    date(2026, 4, 25),
    date(2026, 6, 8),
    date(2026, 12, 25),
    date(2026, 12, 26),
}


def get_day_type(work_date: date) -> str:
    """Determine day type for penalty rate lookup."""
    if work_date in PUBLIC_HOLIDAYS:
        return "public_holiday"
    weekday = work_date.weekday()  # 0=Mon, 6=Sun
    if weekday == 5:
        return "saturday"
    if weekday == 6:
        return "sunday"
    return "weekday"


def calculate_rate(
    classification: str,
    employment_type: str,
    work_date: date,
    start_time: time,
    end_time: time,
    age: Optional[int] = None,
) -> Dict:
    """
    Deterministic rate calculation — no LLM.
    Returns full breakdown with clause citations.
    """
    day_type = get_day_type(work_date)

    # Calculate hours worked
    start_dt = datetime.combine(work_date, start_time)
    end_dt = datetime.combine(work_date, end_time)
    if end_dt <= start_dt:
        end_dt += timedelta(days=1)  # overnight shift
    hours = (end_dt - start_dt).total_seconds() / 3600

    db = SessionLocal()
    try:
        # Build age filter
        if age is not None and age < 21:
            age_filter = "AND age_min <= :age AND (age_max IS NULL OR age_max >= :age)"
        else:
            age_filter = "AND age_min >= 21"

        query = f"""
            SELECT
                rate_per_hour,
                rate_multiplier,
                clause_ref,
                age_min,
                age_max,
                employment_type
            FROM award_rates
            WHERE award_id = :award_id
              AND classification = :classification
              AND employment_type = :employment_type
              AND day_type = :day_type
              {age_filter}
            ORDER BY effective_date DESC
            LIMIT 1
        """

        params = {
            "award_id": AWARD_ID,
            "classification": classification,
            "employment_type": employment_type,
            "day_type": day_type,
            "age": age,
        }

        row = db.execute(text(query), params).fetchone()

        if not row:
            return {
                "error": f"No rate found for {classification}, {employment_type}, age={age}, {day_type}"
            }

        rate_per_hour = float(row.rate_per_hour)
        total_pay = round(rate_per_hour * hours, 2)

        return {
            "classification": classification,
            "employment_type": employment_type,
            "age": age,
            "work_date": work_date.isoformat(),
            "day_type": day_type,
            "start_time": start_time.strftime("%H:%M"),
            "end_time": end_time.strftime("%H:%M"),
            "hours_worked": round(hours, 2),
            "rate_per_hour": rate_per_hour,
            "rate_multiplier": float(row.rate_multiplier),
            "total_pay": total_pay,
            "clause_ref": row.clause_ref,
            "breakdown": _build_breakdown(classification, employment_type, age, day_type, hours, rate_per_hour, row.clause_ref),
        }

    finally:
        db.close()


def _build_breakdown(classification, employment_type, age, day_type, hours, rate, clause_ref) -> str:
    lines = [
        f"Classification: {classification.replace('_', ' ').title()}",
        f"Employment type: {employment_type.replace('_', ' ')}",
    ]
    if age and age < 21:
        lines.append(f"Age: {age} (junior rate applies — {clause_ref})")
    lines += [
        f"Day type: {day_type.replace('_', ' ').title()}",
        f"Hours worked: {round(hours, 2)}",
        f"Rate per hour: ${rate:.4f}",
        f"Total pay: ${round(rate * hours, 2):.2f}",
        f"Award reference: {clause_ref}",
    ]
    return "\n".join(lines)
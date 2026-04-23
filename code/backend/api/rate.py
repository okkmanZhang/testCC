from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import date, time
from utils.rate_calculator import calculate_rate

router = APIRouter()


class RateRequest(BaseModel):
    classification: str      # e.g. "retail_employee_level_1"
    employment_type: str     # "full_time", "part_time", "casual"
    work_date: date          # e.g. "2025-04-19"
    start_time: time         # e.g. "08:00"
    end_time: time           # e.g. "14:00"
    age: Optional[int] = None  # omit for adult rate


@router.post("/rate")
async def get_rate(request: RateRequest):
    result = calculate_rate(
        classification=request.classification,
        employment_type=request.employment_type,
        work_date=request.work_date,
        start_time=request.start_time,
        end_time=request.end_time,
        age=request.age,
    )
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
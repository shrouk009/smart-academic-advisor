from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List


router = APIRouter()


GRADE_POINTS = {
    "A+": 4.0,
    "A": 4.0,
    "A-": 3.7,
    "B+": 3.3,
    "B": 3.0,
    "B-": 2.7,
    "C+": 2.3,
    "C": 2.0,
    "C-": 1.7,
    "D+": 1.3,
    "D": 1.0,
    "F": 0.0
}


class CourseGrade(BaseModel):
    course_name: str
    grade: str
    credit_hours: float = Field(gt=0)


class GPARequest(BaseModel):
    courses: List[CourseGrade]

    previous_cgpa: float | None = Field(
        default=None,
        ge=0,
        le=4
    )

    previous_credit_hours: float = Field(
        default=0,
        ge=0
    )


@router.post("/calculate")
def calculate_gpa(data: GPARequest):

    total_credit_hours = 0
    total_quality_points = 0

    for course in data.courses:

        grade = course.grade.upper().strip()

        if grade not in GRADE_POINTS:
            return {
                "error": f"Invalid grade: {course.grade}"
            }

        grade_point = GRADE_POINTS[grade]

        quality_points = (
            grade_point * course.credit_hours
        )

        total_quality_points += quality_points
        total_credit_hours += course.credit_hours


    if total_credit_hours == 0:
        return {
            "error": "No credit hours entered"
        }


    sgpa = (
        total_quality_points /
        total_credit_hours
    )


    cgpa = None

    if (
        data.previous_cgpa is not None
        and data.previous_credit_hours > 0
    ):

        previous_quality_points = (
            data.previous_cgpa
            * data.previous_credit_hours
        )

        all_quality_points = (
            previous_quality_points
            + total_quality_points
        )

        all_credit_hours = (
            data.previous_credit_hours
            + total_credit_hours
        )

        cgpa = (
            all_quality_points
            / all_credit_hours
        )


    return {
        "sgpa": round(sgpa, 2),
        "cgpa": (
            round(cgpa, 2)
            if cgpa is not None
            else None
        ),
        "current_credit_hours":
            total_credit_hours
    }
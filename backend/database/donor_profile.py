"""Structured education and employment profile for a BloodLink donor."""

from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.database import Base


class DonorProfile(Base):
    """Optional fields are intentionally grouped by a donor's current status."""

    __tablename__ = "donor_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    donor_id: Mapped[int] = mapped_column(
        ForeignKey("donors.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    current_status: Mapped[str] = mapped_column(String(40), nullable=False)

    education_level: Mapped[str | None] = mapped_column(String(40))
    education_level_other: Mapped[str | None] = mapped_column(String(150))
    institution_name: Mapped[str | None] = mapped_column(String(255))
    school_class: Mapped[str | None] = mapped_column(String(40))
    education_board: Mapped[str | None] = mapped_column(String(100))
    education_board_other: Mapped[str | None] = mapped_column(String(150))
    stream: Mapped[str | None] = mapped_column(String(60))
    course_level: Mapped[str | None] = mapped_column(String(100))
    course_level_other: Mapped[str | None] = mapped_column(String(150))
    course_name: Mapped[str | None] = mapped_column(String(150))
    academic_department: Mapped[str | None] = mapped_column(String(150))
    semester_or_year: Mapped[str | None] = mapped_column(String(40))
    university: Mapped[str | None] = mapped_column(String(150))
    expected_graduation_year: Mapped[int | None] = mapped_column(Integer)

    employment_type: Mapped[str | None] = mapped_column(String(60))
    employment_type_other: Mapped[str | None] = mapped_column(String(150))
    occupation: Mapped[str | None] = mapped_column(String(150))
    organization_name: Mapped[str | None] = mapped_column(String(200))
    employment_department: Mapped[str | None] = mapped_column(String(150))
    industry: Mapped[str | None] = mapped_column(String(100))
    industry_other: Mapped[str | None] = mapped_column(String(150))
    work_location: Mapped[str | None] = mapped_column(String(200))
    previous_occupation: Mapped[str | None] = mapped_column(String(150))
    area_of_interest: Mapped[str | None] = mapped_column(String(150))
    status_description: Mapped[str | None] = mapped_column(String(300))

    donor: Mapped["Donor"] = relationship(back_populates="profile")

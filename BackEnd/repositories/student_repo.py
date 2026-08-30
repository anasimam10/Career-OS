"""
Student repository — student-specific queries.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from models.student import Student, StudentProfile
from repositories.base import BaseRepository


class StudentRepository(BaseRepository[Student]):
    def __init__(self, db: Session):
        super().__init__(Student, db)

    def get_by_email(self, email: str) -> Optional[Student]:
        return self._db.query(Student).filter(Student.email == email).first()

    def create_with_profile(self, **kwargs) -> Student:
        """Create a student and an empty StudentProfile in one transaction."""
        student = Student(**kwargs)
        self._db.add(student)
        self._db.flush()  # get student.id

        profile = StudentProfile(student_id=student.id)
        self._db.add(profile)

        self._db.commit()
        self._db.refresh(student)
        return student

    def get_profile(self, student_id: int) -> Optional[StudentProfile]:
        return (
            self._db.query(StudentProfile)
            .filter(StudentProfile.student_id == student_id)
            .first()
        )

    def update_profile(self, student_id: int, **kwargs) -> StudentProfile:
        profile = self.get_profile(student_id)
        if profile is None:
            profile = StudentProfile(student_id=student_id, **kwargs)
            self._db.add(profile)
        else:
            for key, value in kwargs.items():
                setattr(profile, key, value)
        self._db.commit()
        self._db.refresh(profile)
        return profile

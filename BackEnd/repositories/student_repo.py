"""
Student repository — student-specific queries.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from models.student import Student, StudentProfile
from models.roadmap import Roadmap, Milestone
from models.opportunity import StudentOpportunityMatch
from models.mock_interview import MockInterviewSession, MockInterviewQuestion
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

    def delete_student_cascade(self, student_id: int) -> bool:
        """
        Safely, completely, and atomically delete a student and all student-owned records
        respecting foreign-key referential integrity within a single transaction.
        Preserves all global datasets (careers, universities, opportunities, sports, etc.).
        Rolls back the entire transaction if any error occurs.
        """
        student = self._db.query(Student).filter(Student.id == student_id).first()
        if not student:
            return False

        try:
            # 1. Delete mock_interview_questions belonging to student's mock interview sessions
            session_ids = [
                s_id for (s_id,) in self._db.query(MockInterviewSession.id)
                .filter(MockInterviewSession.student_id == student_id).all()
            ]
            if session_ids:
                self._db.query(MockInterviewQuestion).filter(
                    MockInterviewQuestion.session_id.in_(session_ids)
                ).delete(synchronize_session=False)

            # 2. Delete mock_interview_sessions for this student
            self._db.query(MockInterviewSession).filter(
                MockInterviewSession.student_id == student_id
            ).delete(synchronize_session=False)

            # 3. Delete student_opportunity_matches for this student
            self._db.query(StudentOpportunityMatch).filter(
                StudentOpportunityMatch.student_id == student_id
            ).delete(synchronize_session=False)

            # 4. Delete milestones belonging to student's roadmaps
            roadmap_ids = [
                r_id for (r_id,) in self._db.query(Roadmap.id)
                .filter(Roadmap.student_id == student_id).all()
            ]
            if roadmap_ids:
                self._db.query(Milestone).filter(
                    Milestone.roadmap_id.in_(roadmap_ids)
                ).delete(synchronize_session=False)

            # 5. Delete roadmaps for this student
            self._db.query(Roadmap).filter(
                Roadmap.student_id == student_id
            ).delete(synchronize_session=False)

            # 6. Delete student_profiles
            self._db.query(StudentProfile).filter(
                StudentProfile.student_id == student_id
            ).delete(synchronize_session=False)

            # 7. Delete student record
            self._db.delete(student)

            # Commit the atomic transaction
            self._db.commit()

            # Clean up server-side student cache
            try:
                from services.rate_limiter import rate_limiter
                rate_limiter.clear(student_id)
            except Exception:
                pass

            return True
        except Exception:
            self._db.rollback()
            raise

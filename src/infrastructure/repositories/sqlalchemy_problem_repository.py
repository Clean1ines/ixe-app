from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.dialects.sqlite import JSON  # For List[str] fields
from sqlalchemy import String, Integer, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from typing import List, Optional
"""
Implementation of IProblemRepository using SQLAlchemy.

This class provides concrete implementations for persisting and retrieving
Problem entities using a SQL database via SQLAlchemy.
"""
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete  # Add delete import
from src.domain.models.problem import Problem
from src.domain.interfaces.repositories.i_problem_repository import IProblemRepository

logger = logging.getLogger(__name__)

# --- SQLAlchemy ORM Model (DBProblem) ---
# This maps the Problem entity to a database table structure.


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models in this module."""


class DBProblem(Base):
    """
    SQLAlchemy ORM model representing the 'problems' table.

    This model maps the fields of the Problem domain entity to
    database columns.
    """
    __tablename__ = "problems"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Core fields matching Problem entity
    problem_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)  # Maps to Problem.problem_id
    subject_name: Mapped[str] = mapped_column(String, nullable=False)            # Maps to Problem.subject_name
    text: Mapped[str] = mapped_column(String, nullable=False)                    # Maps to Problem.text
    source_url: Mapped[str] = mapped_column(String, nullable=False)              # Maps to Problem.source_url

    # Optional/Computed fields
    difficulty_level: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # Maps to Problem.difficulty_level
    task_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)     # Maps to Problem.task_number
    exam_part: Mapped[Optional[str]] = mapped_column(String, nullable=True)        # Maps to Problem.exam_part

    # Extracted fields
    answer: Mapped[Optional[str]] = mapped_column(String, nullable=True)           # Maps to Problem.answer
    # Use JSON type for List[str] fields
    images: Mapped[List[str]] = mapped_column(JSON, default=list)                  # Maps to Problem.images
    files: Mapped[List[str]] = mapped_column(JSON, default=list)                   # Maps to Problem.files
    kes_codes: Mapped[List[str]] = mapped_column(JSON, default=list)               # Maps to Problem.kes_codes
    topics: Mapped[List[str]] = mapped_column(JSON, default=list)                  # Maps to Problem.topics
    kos_codes: Mapped[List[str]] = mapped_column(JSON, default=list)               # Maps to Problem.kos_codes
    form_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)          # Maps to Problem.form_id

    # FIPI specific
    fipi_proj_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)     # Maps to Problem.fipi_proj_id

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())  # Maps to Problem.created_at
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)            # Maps to Problem.updated_at

    def __repr__(self) -> str:
        return f"DBProblem(id={self.id}, problem_id={self.problem_id!r}, subject_name={self.subject_name!r})"


# --- Repository Implementation ---

class SQLAlchemyProblemRepository(IProblemRepository):
    """
    Implementation of IProblemRepository using SQLAlchemy.

    This class handles the conversion between domain entities (Problem)
    and database models (DBProblem), and executes database operations
    using an AsyncSession.
    """

    def __init__(self, session_factory: 'async_sessionmaker[AsyncSession]'):  # Use string annotation for forward reference
        """
        Initialize the repository with a session factory.

        Args:
            session_factory: A factory to create AsyncSession instances.
                             Typically created with `async_sessionmaker(bind=engine)`.
        """
        self._session_factory = session_factory

    async def save(self, problem: Problem, force_update: bool = False) -> None:  # Add force_update parameter
        """
        Save a Problem entity to the database.

        Args:
            problem: The Problem entity to save.
            force_update: If True, forces updating the problem even if it already exists (e.g., for re-scraping).
                          If False, applies default upsert logic (insert if new, update if exists).
        """
        async with self._session_factory() as session:
            # Check if problem already exists
            result = await session.execute(select(DBProblem).where(DBProblem.problem_id == problem.problem_id))
            existing_db_problem = result.scalar_one_or_none()

            if existing_db_problem and not force_update:
                # Problem exists and force_update is False, maybe update specific fields or just return
                # For now, let's just log and return to keep old behavior if not forced
                logger.debug(f"Problem {problem.problem_id} already exists in DB. Skipping save (not forced).")
                # To truly respect 'not forced', we might not want to update anything here.
                # The current implementation skips *any* update/save if it exists and not forced.
                return

            # Convert Problem entity to DBProblem ORM model attributes
            db_problem_attrs = {
                "problem_id": problem.problem_id,
                "subject_name": problem.subject_name,
                "text": problem.text,
                "source_url": problem.source_url,
                "difficulty_level": problem.difficulty_level,
                "task_number": problem.task_number,
                "exam_part": problem.exam_part,
                "answer": problem.answer,
                "images": problem.images,
                "files": problem.files,
                "kes_codes": problem.kes_codes,
                "topics": problem.topics,
                "kos_codes": problem.kos_codes,
                "form_id": problem.form_id,
                "fipi_proj_id": problem.fipi_proj_id,
                "updated_at": datetime.now()  # Always update the timestamp
            }

            if existing_db_problem:
                if force_update:
                    # Update existing record with new attributes
                    for key, value in db_problem_attrs.items():
                        setattr(existing_db_problem, key, value)
                    logger.debug(f"Updated existing problem in database: {problem.problem_id} (forced update).")
                else:
                    # Default upsert: update existing record with new attributes
                    for key, value in db_problem_attrs.items():
                        setattr(existing_db_problem, key, value)
                    logger.debug(f"Updated existing problem in database: {problem.problem_id}.")
            else:
                # Create new record
                # Add created_at for new records
                db_problem_attrs["created_at"] = problem.created_at  # Use the one from domain entity
                new_db_problem = DBProblem(**db_problem_attrs)
                session.add(new_db_problem)
                logger.debug(f"Inserted new problem to database: {problem.problem_id}.")

            await session.commit()
            logger.debug(f"Saved problem to database: {problem.problem_id} (force_update={force_update})")

    async def clear_subject_problems(self, subject_name: str) -> None:
        """
        Clear all problems for a specific subject.
        This is used when force_restart=True to completely refresh the subject data.

        Args:
            subject_name: The name of the subject to clear
        """
        async with self._session_factory() as session:
            logger.info(f"Clearing all problems for subject: {subject_name}")
            await session.execute(delete(DBProblem).where(DBProblem.subject_name == subject_name))
            await session.commit()
            logger.info(f"Cleared all problems for subject: {subject_name}")

    async def get_by_id(self, problem_id: str) -> Optional[Problem]:
        """
        Retrieve a Problem entity by its unique identifier.

        Args:
            problem_id: The unique identifier (str) of the problem.

        Returns:
            The Problem entity if found, otherwise None.
        """
        async with self._session_factory() as session:  # Use the passed session_factory
            result = await session.execute(select(DBProblem).where(DBProblem.problem_id == problem_id))
            db_problem = result.scalar_one_or_none()
            if db_problem:
                # Convert DBProblem ORM model back to Problem entity
                return self._map_db_to_domain(db_problem)
            return None

    async def get_by_subject(self, subject_name: str) -> List[Problem]:
        """
        Retrieve all Problem entities associated with a specific subject name.

        Args:
            subject_name: The name of the subject (e.g., "Mathematics").

        Returns:
            A list of Problem entities for the given subject name.
        """
        async with self._session_factory() as session:  # Use the passed session_factory
            result = await session.execute(select(DBProblem).where(DBProblem.subject_name == subject_name))
            db_problems = result.scalars().all()
            # Convert list of DBProblem ORM models back to list of Problem entities
            return [self._map_db_to_domain(db_prob) for db_prob in db_problems]

    def _map_db_to_domain(self, db_problem: DBProblem) -> Problem:
        """
        Convert a DBProblem ORM model instance to a Problem domain entity.

        Args:
            db_problem: The DBProblem instance from the database.

        Returns:
            The corresponding Problem domain entity.
        """
        return Problem(
            problem_id=db_problem.problem_id,
            subject_name=db_problem.subject_name,
            text=db_problem.text,
            source_url=db_problem.source_url,
            difficulty_level=db_problem.difficulty_level,
            task_number=db_problem.task_number,
            exam_part=db_problem.exam_part,
            answer=db_problem.answer,
            images=db_problem.images,
            files=db_problem.files,
            kes_codes=db_problem.kes_codes,
            topics=db_problem.topics,
            kos_codes=db_problem.kos_codes,
            form_id=db_problem.form_id,
            fipi_proj_id=db_problem.fipi_proj_id,
            created_at=db_problem.created_at,
            updated_at=db_problem.updated_at
        )

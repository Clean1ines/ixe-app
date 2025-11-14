"""
Integration tests for the SQLAlchemyProblemRepository.

These tests use a real SQLite database (in-memory) to verify that the repository
correctly persists and retrieves Problem entities via SQLAlchemy.
"""
import pytest
import pytest_asyncio # Импортируем pytest_asyncio
import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from src.domain.models.problem import Problem
from src.infrastructure.repositories.sqlalchemy_problem_repository import SQLAlchemyProblemRepository, Base


# Async fixture to create an in-memory SQLite database engine and session
@pytest_asyncio.fixture # Используем pytest_asyncio.fixture
async def db_session():
    """Create an in-memory SQLite database session for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool, # Use StaticPool for in-memory DB
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all) # Create tables

    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback() # Ensure no changes persist between tests if not committed
    await engine.dispose() # Clean up engine resources

# Fixture to create the repository instance
@pytest_asyncio.fixture # Используем pytest_asyncio.fixture и для repository, так как он зависит от db_session
async def repository(db_session):
    """Create a SQLAlchemyProblemRepository instance."""
    session_factory = sessionmaker(db_session.bind, class_=AsyncSession, expire_on_commit=False)
    return SQLAlchemyProblemRepository(session_factory)

# Fixture for a sample Problem entity (синхронная, не зависит от асинхронных ресурсов)
@pytest.fixture
def sample_problem():
    """Create a sample Problem entity for testing."""
    return Problem(
        problem_id="test_id_123",
        subject_name="Mathematics",
        text="Solve for x: x + 2 = 5",
        source_url="https://fipi.ru/test",
        answer="3",
        images=["image1.png"],
        files=["data.csv"],
        kes_codes=["1.1"],
        topics=["Algebra"],
        kos_codes=["3.2"],
        form_id="form_123",
        fipi_proj_id="proj_abc",
        difficulty_level="basic",
        task_number=1,
        exam_part="Part 1"
    )

@pytest.mark.asyncio
async def test_save_and_get_by_id(repository, sample_problem, db_session):
    """Test saving a problem and retrieving it by ID."""
    # Save the problem
    await repository.save(sample_problem)

    # Retrieve the problem by ID
    retrieved_problem = await repository.get_by_id(sample_problem.problem_id)

    # Assert that the retrieved problem matches the original
    assert retrieved_problem is not None
    assert retrieved_problem == sample_problem # Uses __eq__ based on problem_id
    assert retrieved_problem.text == sample_problem.text
    assert retrieved_problem.subject_name == sample_problem.subject_name
    assert retrieved_problem.answer == sample_problem.answer
    assert retrieved_problem.images == sample_problem.images
    assert retrieved_problem.difficulty_level == sample_problem.difficulty_level
    assert retrieved_problem.task_number == sample_problem.task_number
    # ... assert other fields as needed

@pytest.mark.asyncio
async def test_get_by_id_not_found(repository):
    """Test retrieving a problem by ID that does not exist."""
    retrieved_problem = await repository.get_by_id("non_existent_id")
    assert retrieved_problem is None

@pytest.mark.asyncio
async def test_save_and_get_by_subject(repository, sample_problem, db_session):
    """Test saving multiple problems and retrieving them by subject."""
    subject = "Physics"
    problem1 = Problem(
        problem_id="phys_001",
        subject_name=subject,
        text="What is gravity?",
        source_url="https://fipi.ru/phys1"
    )
    problem2 = Problem(
        problem_id="phys_002",
        subject_name=subject,
        text="What is velocity?",
        source_url="https://fipi.ru/phys2"
    )
    other_subject_problem = Problem(
        problem_id="chem_001",
        subject_name="Chemistry",
        text="What is an atom?",
        source_url="https://fipi.ru/chem1"
    )

    # Save problems
    await repository.save(problem1)
    await repository.save(problem2)
    await repository.save(other_subject_problem)

    # Retrieve problems by subject
    retrieved_problems = await repository.get_by_subject(subject)

    # Assert that the correct problems were retrieved
    assert len(retrieved_problems) == 2
    retrieved_ids = {p.problem_id for p in retrieved_problems}
    assert retrieved_ids == {"phys_001", "phys_002"}
    # Check content of one of the retrieved problems
    phys_001 = next((p for p in retrieved_problems if p.problem_id == "phys_001"), None)
    assert phys_001 is not None
    assert phys_001.text == "What is gravity?"

if __name__ == "__main__":
    pytest.main(["-v", __file__, "-k", "async"])

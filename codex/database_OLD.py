"""
Database setup and management for Codex patterns.

Using SQLModel with SQLite for pattern storage.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession as SQLModelAsyncSession

from .models import Pattern, PatternCategory, PatternPriority
from .settings import settings


class Database:
    """Database manager for Codex patterns."""

    def __init__(self, db_path: str | None = None):
        """Initialize database connection."""
        if db_path is None:
            # Default to data/patterns.db in package directory
            data_dir = Path(__file__).parent / "data"
            data_dir.mkdir(exist_ok=True)
            self.db_path = data_dir / settings.database_path
        else:
            self.db_path = Path(db_path)
        self.db_url = f"sqlite+aiosqlite:///{self.db_path}"
        self.engine = create_async_engine(
            self.db_url,
            echo=False,
            future=True,
        )

    async def init_db(self) -> None:
        """Initialize database schema."""
        async with self.engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session."""
        async with SQLModelAsyncSession(self.engine) as session:
            yield session

    async def add_pattern(self, pattern: Pattern) -> Pattern:
        """Add a new pattern to the database."""
        async with self.get_session() as session:
            session.add(pattern)
            await session.commit()
            await session.refresh(pattern)
            return pattern

    async def get_pattern(self, pattern_id: int) -> Pattern | None:
        """Get a pattern by ID."""
        async with self.get_session() as session:
            statement = select(Pattern).where(Pattern.id == pattern_id)
            result = await session.exec(statement)
            return result.first()

    async def get_patterns_by_category(self, category: PatternCategory) -> list[Pattern]:
        """Get all patterns in a category."""
        async with self.get_session() as session:
            statement = select(Pattern).where(Pattern.category == category)
            result = await session.exec(statement)
            return list(result.all())

    async def get_patterns_by_priority(self, priority: PatternPriority) -> list[Pattern]:
        """Get all patterns with a specific priority."""
        async with self.get_session() as session:
            statement = select(Pattern).where(Pattern.priority == priority)
            result = await session.exec(statement)
            return list(result.all())

    async def search_patterns(self, query: str) -> list[Pattern]:
        """Search patterns by name or description."""
        async with self.get_session() as session:
            statement = select(Pattern).where(
                (Pattern.name.contains(query)) | (Pattern.description.contains(query))  # type: ignore[union-attr]
            )
            result = await session.exec(statement)
            return list(result.all())

    async def get_all_patterns(self) -> list[Pattern]:
        """Get all patterns from the database."""
        async with self.get_session() as session:
            statement = select(Pattern)
            result = await session.exec(statement)
            return list(result.all())

    async def update_pattern_usage(self, pattern_id: int, success: bool = True) -> None:
        """Update pattern usage statistics."""
        async with self.get_session() as session:
            pattern = await self.get_pattern(pattern_id)
            if pattern:
                pattern.usage_count += 1
                if success:
                    pattern.success_rate = (
                        pattern.success_rate * (pattern.usage_count - 1) + 1.0
                    ) / pattern.usage_count
                else:
                    pattern.success_rate = (
                        pattern.success_rate * (pattern.usage_count - 1)
                    ) / pattern.usage_count
                session.add(pattern)
                await session.commit()

    async def close(self) -> None:
        """Close database connection."""
        await self.engine.dispose()
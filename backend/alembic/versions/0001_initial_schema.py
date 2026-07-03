"""initial schema — all 24 tables

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-06-30

This baseline migration materialises the full schema described by the
SQLAlchemy models (24 tables, foreign keys, indexes and the properties
full-text GIN index). It builds straight from Base.metadata so it always
matches the models exactly. Subsequent changes should be created with
`alembic revision --autogenerate -m "..."`.
"""
from typing import Sequence, Union

from alembic import op

from app.db.base import Base

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
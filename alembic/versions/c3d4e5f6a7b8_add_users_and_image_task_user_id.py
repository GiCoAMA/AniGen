"""add users table and image_tasks.user_id

Revision ID: c3d4e5f6a7b8
Revises: 8f1a2b3c4d5e
Create Date: 2025-03-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "8f1a2b3c4d5e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="1", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=False)

    with op.batch_alter_table("image_tasks") as batch_op:
        batch_op.add_column(sa.Column("user_id", sa.Integer(), nullable=True))
        batch_op.create_index("ix_image_tasks_user_id", ["user_id"], unique=False)
        batch_op.create_foreign_key(
            "fk_image_tasks_user_id_users",
            "users",
            ["user_id"],
            ["id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("image_tasks") as batch_op:
        batch_op.drop_constraint("fk_image_tasks_user_id_users", type_="foreignkey")
        batch_op.drop_index("ix_image_tasks_user_id")
        batch_op.drop_column("user_id")

    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")

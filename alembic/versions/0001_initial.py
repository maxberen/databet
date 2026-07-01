"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-06-18
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLE_KW = dict(
    mysql_engine="InnoDB",
    mysql_charset="utf8mb4",
    mysql_collate="utf8mb4_unicode_ci",
)


def upgrade() -> None:
    op.create_table(
        "sources",
        sa.Column("id", mysql.INTEGER(unsigned=True), autoincrement=True, primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("base_url", sa.String(255), nullable=False),
        sa.Column("type", sa.Enum("api", "browser", name="sourcetype"), nullable=False),
        sa.Column("is_active", mysql.TINYINT(1), nullable=False, server_default=sa.text("1")),
        sa.Column("requires_auth", mysql.TINYINT(1), nullable=False, server_default=sa.text("0")),
        sa.Column("credentials", mysql.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            server_onupdate=sa.text("CURRENT_TIMESTAMP"),
        ),
        **_TABLE_KW,
    )

    op.create_table(
        "source_protocols",
        sa.Column("id", mysql.INTEGER(unsigned=True), autoincrement=True, primary_key=True),
        sa.Column("source_id", mysql.INTEGER(unsigned=True), nullable=False),
        sa.Column("login_flow", mysql.JSON(), nullable=True),
        sa.Column("odds_navigation", mysql.JSON(), nullable=True),
        sa.Column("selector_map", mysql.JSON(), nullable=True),
        sa.Column("rate_limit_ms", sa.Integer(), nullable=False, server_default=sa.text("1500")),
        sa.Column("requires_captcha", mysql.TINYINT(1), nullable=False, server_default=sa.text("0")),
        sa.Column("captcha_service", sa.String(50), nullable=True),
        sa.Column("human_profile", mysql.JSON(), nullable=True),
        sa.Column("session_max_minutes", sa.Integer(), nullable=False, server_default=sa.text("30")),
        sa.Column("notes", sa.String(1000), nullable=True),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"]),
        **_TABLE_KW,
    )

    op.create_table(
        "matches",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, primary_key=True),
        sa.Column("source_id", mysql.INTEGER(unsigned=True), nullable=False),
        sa.Column("sport", sa.Enum("football", "tennis", name="sport"), nullable=False),
        sa.Column("competition", sa.String(150), nullable=True),
        sa.Column("home_team", sa.String(150), nullable=True),
        sa.Column("away_team", sa.String(150), nullable=True),
        sa.Column("match_datetime", sa.DateTime(), nullable=True),
        sa.Column("scraped_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("raw_data", mysql.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"]),
        **_TABLE_KW,
    )
    op.create_index("idx_sport_date", "matches", ["sport", "match_datetime"])
    op.create_index("idx_scraped", "matches", ["scraped_at"])

    op.create_table(
        "odds",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, primary_key=True),
        sa.Column("match_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("source_id", mysql.INTEGER(unsigned=True), nullable=False),
        sa.Column("scraped_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("home_win", sa.DECIMAL(10, 4), nullable=True),
        sa.Column("draw", sa.DECIMAL(10, 4), nullable=True),
        sa.Column("away_win", sa.DECIMAL(10, 4), nullable=True),
        sa.Column("player1_win", sa.DECIMAL(10, 4), nullable=True),
        sa.Column("player2_win", sa.DECIMAL(10, 4), nullable=True),
        sa.Column("bookmaker", sa.String(100), nullable=True),
        sa.ForeignKeyConstraint(["match_id"], ["matches.id"]),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"]),
        **_TABLE_KW,
    )
    op.create_index("idx_match_source", "odds", ["match_id", "source_id"])

    op.create_table(
        "scrape_sessions",
        sa.Column("id", mysql.INTEGER(unsigned=True), autoincrement=True, primary_key=True),
        sa.Column("source_id", mysql.INTEGER(unsigned=True), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("running", "success", "failed", "blocked", name="sessionstatus"),
            nullable=False,
        ),
        sa.Column("matches_found", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("proxy_used", sa.String(100), nullable=True),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"]),
        **_TABLE_KW,
    )


def downgrade() -> None:
    op.drop_table("scrape_sessions")
    op.drop_index("idx_match_source", table_name="odds")
    op.drop_table("odds")
    op.drop_index("idx_scraped", table_name="matches")
    op.drop_index("idx_sport_date", table_name="matches")
    op.drop_table("matches")
    op.drop_table("source_protocols")
    op.drop_table("sources")

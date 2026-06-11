"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-06-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON


revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'jobs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('status', sa.Enum('pending', 'processing', 'completed', 'failed', name='jobstatus'), nullable=False, server_default='pending'),
        sa.Column('row_count_raw', sa.Integer(), nullable=True),
        sa.Column('row_count_clean', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('progress', sa.Integer(), nullable=True, server_default='0'),
    )

    op.create_table(
        'transactions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('job_id', UUID(as_uuid=True), sa.ForeignKey('jobs.id'), nullable=False),
        sa.Column('txn_id', sa.String(), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('merchant', sa.String(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('account_id', sa.String(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_anomaly', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('anomaly_reason', sa.Text(), nullable=True),
        sa.Column('llm_category', sa.String(), nullable=True),
        sa.Column('llm_raw_response', sa.Text(), nullable=True),
        sa.Column('llm_failed', sa.Boolean(), nullable=True, server_default='false'),
    )

    op.create_table(
        'job_summaries',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('job_id', UUID(as_uuid=True), sa.ForeignKey('jobs.id'), nullable=False, unique=True),
        sa.Column('total_spend_inr', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('total_spend_usd', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('top_merchants', JSON(), nullable=True),
        sa.Column('anomaly_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('narrative', sa.Text(), nullable=True),
        sa.Column('risk_level', sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('job_summaries')
    op.drop_table('transactions')
    op.drop_table('jobs')
    op.execute('DROP TYPE IF EXISTS jobstatus')

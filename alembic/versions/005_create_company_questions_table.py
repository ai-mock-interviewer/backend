"""Create company_questions table

Revision ID: 005
Revises: 004
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create company_questions table
    op.create_table('company_questions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('question_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_company_questions_id'), 'company_questions', ['id'], unique=False)
    op.create_index(op.f('ix_company_questions_company_id'), 'company_questions', ['company_id'], unique=False)
    op.create_index(op.f('ix_company_questions_question_id'), 'company_questions', ['question_id'], unique=False)
    
    # Create unique constraint to prevent duplicate company-question pairs
    op.create_index('ix_company_questions_unique', 'company_questions', ['company_id', 'question_id'], unique=True)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_company_questions_unique', table_name='company_questions')
    op.drop_index(op.f('ix_company_questions_question_id'), table_name='company_questions')
    op.drop_index(op.f('ix_company_questions_company_id'), table_name='company_questions')
    op.drop_index(op.f('ix_company_questions_id'), table_name='company_questions')
    
    # Drop table
    op.drop_table('company_questions')

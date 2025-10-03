"""Enable pgvector extension and update resumes table

Revision ID: 006
Revises: 005
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Update the embedding_vector column to use native vector type
    # First, drop the old column
    op.drop_column('resumes', 'embedding_vector')
    
    # Add the new vector column
    op.add_column('resumes', sa.Column('embedding_vector', Vector(384), nullable=True))
    
    # Create index for vector similarity search
    op.execute('CREATE INDEX IF NOT EXISTS ix_resumes_embedding_vector ON resumes USING ivfflat (embedding_vector vector_cosine_ops) WITH (lists = 100)')


def downgrade() -> None:
    # Drop the vector index
    op.execute('DROP INDEX IF EXISTS ix_resumes_embedding_vector')
    
    # Drop the vector column
    op.drop_column('resumes', 'embedding_vector')
    
    # Add back the old string column
    op.add_column('resumes', sa.Column('embedding_vector', sa.String(), nullable=True))
    
    # Note: We don't drop the vector extension as it might be used by other tables

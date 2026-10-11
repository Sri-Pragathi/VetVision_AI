"""add enhanced pet profile fields

Revision ID: 4b3c2d1e0f9a
Revises: 7a8b9c0d1e2f
Create Date: 2026-10-10 21:58:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4b3c2d1e0f9a'
down_revision = '7a8b9c0d1e2f'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('pets', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('weight_unit', sa.String(length=10), nullable=True, server_default='kg')
        )
        batch_op.add_column(
            sa.Column('photo_url', sa.String(length=500), nullable=True)
        )
        batch_op.add_column(
            sa.Column('spayed_neutered', sa.Boolean(), nullable=True)
        )
        batch_op.add_column(
            sa.Column('vaccination_history', sa.Text(), nullable=True)
        )
        batch_op.add_column(
            sa.Column('medical_history', sa.Text(), nullable=True)
        )
        batch_op.add_column(
            sa.Column('notes', sa.Text(), nullable=True)
        )


def downgrade():
    with op.batch_alter_table('pets', schema=None) as batch_op:
        batch_op.drop_column('notes')
        batch_op.drop_column('medical_history')
        batch_op.drop_column('vaccination_history')
        batch_op.drop_column('spayed_neutered')
        batch_op.drop_column('photo_url')
        batch_op.drop_column('weight_unit')

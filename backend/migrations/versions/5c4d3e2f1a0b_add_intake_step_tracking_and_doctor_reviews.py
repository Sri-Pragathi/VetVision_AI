"""add intake step tracking and doctor reviews

Revision ID: 5c4d3e2f1a0b
Revises: 4b3c2d1e0f9a
Create Date: 2026-10-10 22:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5c4d3e2f1a0b'
down_revision = '4b3c2d1e0f9a'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Add current_step and draft_data to health_assessments table
    with op.batch_alter_table('health_assessments', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('current_step', sa.Integer(), nullable=False, server_default='1')
        )
        batch_op.add_column(
            sa.Column('draft_data', sa.JSON(), nullable=True)
        )

    # 2. Create doctor_reviews table
    op.create_table(
        'doctor_reviews',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('assessment_id', sa.String(length=36), nullable=False),
        sa.Column('doctor_id', sa.String(length=36), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='reviewed'),
        sa.Column('override_triage_level', sa.String(length=20), nullable=True),
        sa.Column('doctor_notes', sa.Text(), nullable=True),
        sa.Column('recommendations', sa.Text(), nullable=True),
        sa.Column('prescriptions', sa.Text(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['assessment_id'], ['health_assessments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['doctor_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_doctor_reviews_assessment_id'), 'doctor_reviews', ['assessment_id'], unique=False)
    op.create_index(op.f('ix_doctor_reviews_doctor_id'), 'doctor_reviews', ['doctor_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_doctor_reviews_doctor_id'), table_name='doctor_reviews')
    op.drop_index(op.f('ix_doctor_reviews_assessment_id'), table_name='doctor_reviews')
    op.drop_table('doctor_reviews')

    with op.batch_alter_table('health_assessments', schema=None) as batch_op:
        batch_op.drop_column('draft_data')
        batch_op.drop_column('current_step')

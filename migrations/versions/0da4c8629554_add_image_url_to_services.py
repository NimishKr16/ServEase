"""Add image url to services

Revision ID: 0da4c8629554
Revises: 4bf05b96ba00
Create Date: 2024-10-13 15:25:29.487175

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0da4c8629554'
down_revision = '4bf05b96ba00'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('services', schema=None) as batch_op:
        batch_op.add_column(sa.Column('image_url', sa.String(length=255), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('services', schema=None) as batch_op:
        batch_op.drop_column('image_url')

    # ### end Alembic commands ###

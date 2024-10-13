"""Add image url

Revision ID: 4bf05b96ba00
Revises: 9053fd7d428f
Create Date: 2024-10-13 15:06:31.351311

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4bf05b96ba00'
down_revision = '9053fd7d428f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('customers', schema=None) as batch_op:
        batch_op.drop_column('image_url')

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('image_url', sa.String(length=255), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('image_url')

    with op.batch_alter_table('customers', schema=None) as batch_op:
        batch_op.add_column(sa.Column('image_url', sa.VARCHAR(length=255), nullable=True))

    # ### end Alembic commands ###
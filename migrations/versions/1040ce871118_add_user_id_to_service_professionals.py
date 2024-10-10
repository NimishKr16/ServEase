"""Add user_id to service_professionals

Revision ID: 1040ce871118
Revises: 
Create Date: 2024-10-10 11:50:29.442871

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1040ce871118'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    
    # Altering the customers table
    with op.batch_alter_table('customers', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))
        batch_op.alter_column('pin_code',
               existing_type=sa.VARCHAR(length=10),
               nullable=True)
        # Create a foreign key constraint with a specific name
        batch_op.create_foreign_key('fk_user_customers', 'users', ['user_id'], ['id'])

    # Altering the service_professionals table
    with op.batch_alter_table('service_professionals', schema=None) as batch_op:
        batch_op.alter_column('experience',
               existing_type=sa.INTEGER(),
               nullable=True)
        # Create a foreign key constraint with a specific name
        batch_op.create_foreign_key('fk_user_service_professionals', 'users', ['user_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('service_professionals', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.alter_column('experience',
               existing_type=sa.INTEGER(),
               nullable=False)

    with op.batch_alter_table('customers', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.alter_column('pin_code',
               existing_type=sa.VARCHAR(length=10),
               nullable=False)
        batch_op.drop_column('user_id')

    # ### end Alembic commands ###

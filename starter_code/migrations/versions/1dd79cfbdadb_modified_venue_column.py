"""modified venue column

Revision ID: 1dd79cfbdadb
Revises: d8b54fb9e20b
Create Date: 2020-04-07 21:06:21.852646

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1dd79cfbdadb'
down_revision = 'd8b54fb9e20b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('venue', sa.Column('seeking_talent', sa.Boolean(), nullable=True))
    op.drop_column('venue', 'seeking_venue')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('venue', sa.Column('seeking_venue', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.drop_column('venue', 'seeking_talent')
    # ### end Alembic commands ###

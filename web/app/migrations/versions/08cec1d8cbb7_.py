"""empty message

Revision ID: 08cec1d8cbb7
Revises: 6b244d58e52c
Create Date: 2018-09-03 20:14:34.980901

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '08cec1d8cbb7'
down_revision = '6b244d58e52c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_ad_search_vector', table_name='ad')
    op.drop_column('ad', 'search_vector')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('ad', sa.Column('search_vector', postgresql.TSVECTOR(), autoincrement=False, nullable=True))
    op.create_index('ix_ad_search_vector', 'ad', ['search_vector'], unique=False)
    # ### end Alembic commands ###

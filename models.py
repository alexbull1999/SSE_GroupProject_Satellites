from sqlalchemy import Table, Column, Integer, String, MetaData
from sqlalchemy.orm import declarative_base

Base = declarative_base()
metadata = MetaData()

# define satellite table

satellite_table = Table(
    'satellite',
    Base.metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String),
)


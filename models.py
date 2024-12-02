from numbers import Real
from sqlalchemy import Table, Column, Integer, String, MetaData, Float
from sqlalchemy.orm import declarative_base

Base = declarative_base()
metadata = MetaData()

# define satellite table

satellite_table = Table(
    "satellite",
    Base.metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String),
)

country_table = Table(
    "country",
    Base.metadata,
    Column("country", String, primary_key=True),
    Column("latitude", Float),
    Column("longitude", Float),
    Column("name", String),
    Column("area", Float),
    Column("above_angle", Float),
)

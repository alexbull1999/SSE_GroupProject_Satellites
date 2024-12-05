from sqlalchemy import (
    Table,
    Column,
    Integer,
    String,
    MetaData,
    Float,
    ForeignKey,
)
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

# Define the User table
user_table = Table(
    "user",
    Base.metadata,
    Column("id", Integer, primary_key=True),
    Column("user_name", String, unique=True, nullable=False),
)

user_satellite_table = Table(
    "user_satellite",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("user.id"), primary_key=True),
    Column(
        "satellite_id", Integer, ForeignKey("satellite.id"), primary_key=True
    ),
    # UniqueConstraint('user_id', 'satellite_id', name='unique_user_satellite')
    # UniqueConstraint means a user can only have on of each satellite. need to add extra stuff ot make work
)

user_country_table = Table(
    "user_country",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("user.id"), primary_key=True),
    Column("country_name", String, ForeignKey("country.name"), primary_key=True),
)
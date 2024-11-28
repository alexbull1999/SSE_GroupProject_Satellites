from sqlalchemy import Table, Column, Integer, String, ForeignKey, MetaData

metadata = MetaData()

# define satellite table

satelliteTable = Table(
    "satellite",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(255), nullable=False),
)

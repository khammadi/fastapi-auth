import sqlalchemy
from sqlalchemy import Column, Integer, String, MetaData, Table

metadata = MetaData()

users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("email", String, unique=True, index=True),
    Column("name", String),
)
import os
from databases import Database

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:pass123@localhost:5432/fastapidb")

database = Database(DATABASE_URL)
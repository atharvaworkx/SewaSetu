import os
import psycopg2
import configparser

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

config = configparser.ConfigParser()
config.read(os.path.join(BASE_DIR, "config", "app.ini"))

conn = psycopg2.connect(
    host=os.environ.get("DATABASE_HOST", config.get("database", "host")),
    port=os.environ.get("DATABASE_PORT", config.get("database", "port")),
    dbname=os.environ.get("DATABASE_NAME", config.get("database", "name")),
    user=os.environ.get("DATABASE_USER", config.get("database", "user")),
    password=os.environ.get("DATABASE_PASSWORD", config.get("database", "password")),
)

cur = conn.cursor()

with open(os.path.join(BASE_DIR, "schema.sql"), "r") as f:
    schema = f.read()
    cur.execute(schema)

conn.commit()
cur.close()
conn.close()

print("Database initialized successfully!")

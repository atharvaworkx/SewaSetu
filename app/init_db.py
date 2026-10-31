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

print("Creating tables...")
with open(os.path.join(BASE_DIR, "schema.sql"), "r") as f:
    schema = f.read()
    cur.execute(schema)
    
print("Loading 1K citizen records...")
seed_file = os.path.join(BASE_DIR, "seed_1k.sql")
if os.path.exists(seed_file):
    with open(seed_file, "r", encoding="utf-8") as f:
        seed_data = f.read()
        cur.execute(seed_data)
    print("✅ Loaded 1000 sample records")
else:
    print("⚠️  seed_1k.sql not found, skipping seed data")

conn.commit()
cur.close()
conn.close()

print("Database initialized successfully!")

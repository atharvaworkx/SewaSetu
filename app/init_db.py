import os
import configparser
import psycopg2

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

config = configparser.ConfigParser()
config.read(os.path.join(BASE_DIR, "config", "app.ini"))

db_url = os.environ.get("DATABASE_URL")
if db_url:
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    conn = psycopg2.connect(db_url)
else:
    conn = psycopg2.connect(
        host=os.environ.get("DATABASE_HOST", config.get("database", "host")),
        port=os.environ.get("DATABASE_PORT", config.get("database", "port")),
        dbname=os.environ.get("DATABASE_NAME", config.get("database", "name")),
        user=os.environ.get("DATABASE_USER", config.get("database", "user")),
        password=os.environ.get("DATABASE_PASSWORD", config.get("database", "password")),
    )

cur = conn.cursor()

print("Creating tables...")
with open(os.path.join(BASE_DIR, "schema.sql"), "r", encoding="utf-8") as f:
    schema = f.read()
    cur.execute(schema)
conn.commit()

# Check existing record counts
cur.execute("SELECT COUNT(*) FROM applications;")
app_count = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM portal_users;")
user_count = cur.fetchone()[0]
print(f"Current database records: {app_count} applications, {user_count} portal users")

seed_file = os.path.join(BASE_DIR, "seed_1k.sql")
if os.path.exists(seed_file):
    if app_count >= 1000 and user_count >= 1000:
        print(f"✅ Database already seeded ({app_count} applications, {user_count} portal users). Skipping seed.")
    else:
        print("Loading citizen seed records (idempotent ON CONFLICT)...")
        try:
            with open(seed_file, "r", encoding="utf-8") as f:
                seed_data = f.read()
                cur.execute(seed_data)
            conn.commit()
            cur.execute("SELECT COUNT(*) FROM applications;")
            new_app_count = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM portal_users;")
            new_user_count = cur.fetchone()[0]
            print(f"✅ Seeding complete. Database now has {new_app_count} applications, {new_user_count} portal users")
        except psycopg2.IntegrityError as e:
            conn.rollback()
            print(f"⚠️  Notice: Conflicting records detected ({e}). Continuing with existing data.")
        except Exception as e:
            conn.rollback()
            print(f"⚠️  Warning while processing seed data: {e}. Continuing startup.")
else:
    print("⚠️  seed_1k.sql not found, skipping seed data")

# Ensure applications ID sequence is properly aligned with max(id)
try:
    cur.execute("SELECT setval('applications_id_seq', COALESCE((SELECT MAX(id) FROM applications), 1));")
    conn.commit()
except Exception as e:
    conn.rollback()
    print(f"⚠️  Warning setting sequence value: {e}")

cur.close()
conn.close()

print("Database initialized successfully!")

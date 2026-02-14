
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def init_db():
    db_url = os.getenv("SUPABASE_DATABASE_URL")
    if not db_url:
        print("❌ Error: SUPABASE_DATABASE_URL is not set in .env")
        print("Please fetch your connection string from Supabase Dashboard > Settings > Database > Connection String > URI")
        print("Format: postgres://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres")
        return

    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    if not os.path.exists(schema_path):
        print(f"❌ Error: schema.sql not found at {schema_path}")
        return

    with open(schema_path, "r") as f:
        schema_sql = f.read()

    try:
        print("🔌 Connecting to database...")
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        print("🚀 Executing schema migration...")
        cur.execute(schema_sql)
        conn.commit()
        
        cur.close()
        conn.close()
        print("✅ Database schema initialized successfully!")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")

if __name__ == "__main__":
    init_db()

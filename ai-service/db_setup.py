import psycopg2
import os

DATABASE_URL = "postgresql://postgres:fixloopai636@db.boepdarunbvfpxhcjsef.supabase.co:5432/postgres"

def run_sql_file(conn, filepath):
    print(f"Executing {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        sql = f.read()
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()
    print(f"Done: {filepath}")

def main():
    print("Connecting to Supabase...")
    conn = psycopg2.connect(DATABASE_URL)
    
    base_dir = r"d:\FixLoop AI\fixloop-ai\supabase"
    
    migrations = [
        "migrations/00001_enable_pgvector.sql",
        "migrations/00002_create_enums.sql",
        "migrations/00003_create_tables.sql",
        "migrations/00004_rls_policies.sql",
        "migrations/00005_functions_triggers.sql",
        "migrations/00006_fix_recommendations_extra_cols.sql",
        "seed/seed.sql"
    ]
    
    for mig in migrations:
        path = os.path.join(base_dir, mig.replace('/', '\\'))
        try:
            run_sql_file(conn, path)
        except Exception as e:
            print(f"Error executing {mig}: {e}")
            conn.rollback()

    print("\nVerifying row counts:")
    tables = [
        "tickets",
        "ticket_clusters",
        "deployments",
        "investigations",
        "fix_recommendations",
        "validation_results"
    ]
    
    for table in tables:
        try:
            with conn.cursor() as cur:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                count = cur.fetchone()[0]
                print(f"{table}: {count}")
        except Exception as e:
            print(f"{table}: Error - {e}")
            conn.rollback()
            
    conn.close()

if __name__ == '__main__':
    main()

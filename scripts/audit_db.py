import asyncio
import asyncpg
import json
import os
from datetime import datetime

DATABASE_URL = "postgresql://postgres:postgres@127.0.0.1:54322/postgres"
SEED_FILE = "supabase/seed/seed.sql"

async def main():
    print("Connecting to database...")
    try:
        conn = await asyncpg.connect(DATABASE_URL)
    except Exception as e:
        print(f"Failed to connect to {DATABASE_URL}: {e}")
        return

    print("Running Task 1: Database Seed...")
    # First, truncate tables to ensure clean seed
    tables = [
        "cluster_tickets", "tickets", "investigation_evidence", 
        "validation_results", "fix_recommendations", "investigations", 
        "ticket_clusters", "deployments"
    ]
    for t in tables:
        await conn.execute(f"TRUNCATE TABLE public.{t} CASCADE;")

    # Execute seed.sql
    with open(SEED_FILE, "r") as f:
        seed_sql = f.read()
    
    await conn.execute(seed_sql)
    print("Database seeded successfully.")

    print("\n--- TASK 1: DATABASE COUNTS ---")
    
    counts = {}
    for t in tables:
        count = await conn.fetchval(f"SELECT COUNT(*) FROM public.{t}")
        counts[t] = count
        print(f"{t}: {count}")

    print("\n--- TASK 2: DATA INTEGRITY AUDIT ---")
    
    # 1. Foreign keys: Tickets with invalid or no cluster assignment
    # Actually, tickets can exist without cluster assignment if they are unclustered.
    # The requirement says "missing cluster assignments". We'll check how many tickets are in cluster_tickets vs total.
    clustered_tickets = await conn.fetchval("SELECT COUNT(DISTINCT ticket_id) FROM public.cluster_tickets")
    total_tickets = counts["tickets"]
    unassigned_tickets = total_tickets - clustered_tickets
    print(f"Tickets missing cluster assignments: {unassigned_tickets} out of {total_tickets}")

    # 2. Orphan records: Investigations without clusters
    orphan_inv = await conn.fetchval("SELECT COUNT(*) FROM public.investigations WHERE cluster_id NOT IN (SELECT id FROM public.ticket_clusters)")
    print(f"Orphan investigations: {orphan_inv}")

    # 3. Invalid references: Recommendations with invalid investigation_id
    orphan_rec = await conn.fetchval("SELECT COUNT(*) FROM public.fix_recommendations WHERE investigation_id IS NOT NULL AND investigation_id NOT IN (SELECT id FROM public.investigations)")
    print(f"Orphan recommendations: {orphan_rec}")

    # 4. Duplicate ticket ids
    duplicate_external = await conn.fetchval("""
        SELECT COUNT(*) FROM (
            SELECT external_id, COUNT(*) FROM public.tickets GROUP BY external_id HAVING COUNT(*) > 1
        ) as dupes
    """)
    print(f"Duplicate ticket external IDs: {duplicate_external}")

    # 5. Invalid deployment links
    invalid_deploy_tickets = await conn.fetchval("SELECT COUNT(*) FROM public.tickets WHERE related_deploy_id IS NOT NULL AND related_deploy_id NOT IN (SELECT id FROM public.deployments)")
    invalid_deploy_clusters = await conn.fetchval("SELECT COUNT(*) FROM public.ticket_clusters WHERE related_deploy_id IS NOT NULL AND related_deploy_id NOT IN (SELECT id FROM public.deployments)")
    invalid_deploy_inv = await conn.fetchval("SELECT COUNT(*) FROM public.investigations WHERE deploy_correlation_id IS NOT NULL AND deploy_correlation_id NOT IN (SELECT id FROM public.deployments)")
    print(f"Invalid deployment links in tickets: {invalid_deploy_tickets}")
    print(f"Invalid deployment links in clusters: {invalid_deploy_clusters}")
    print(f"Invalid deployment links in investigations: {invalid_deploy_inv}")

    # Build report dict
    report = {
        "counts": counts,
        "integrity": {
            "unassigned_tickets": unassigned_tickets,
            "orphan_investigations": orphan_inv,
            "orphan_recommendations": orphan_rec,
            "duplicate_external_ids": duplicate_external,
            "invalid_deployment_links": invalid_deploy_tickets + invalid_deploy_clusters + invalid_deploy_inv
        }
    }

    with open("audit_db_results.json", "w") as f:
        json.dump(report, f, indent=2)

    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())

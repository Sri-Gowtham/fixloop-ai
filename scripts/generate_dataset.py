import csv
import json
import random
import uuid
from datetime import datetime, timedelta
import os

SEED_DIR = "supabase/seed"
os.makedirs(SEED_DIR, exist_ok=True)

# ---------------------------------------------------------
# Configurations
# ---------------------------------------------------------
NUM_TICKETS = 5000

DEPLOYMENTS = [
    {"id": f"DEP-{uuid.uuid4().hex[:8]}", "version": "v2.4.1", "title": "Patch release 2.4.1", "risk": "low", "date": datetime.utcnow() - timedelta(days=30)},
    {"id": f"DEP-{uuid.uuid4().hex[:8]}", "version": "v2.4.2", "title": "CSV Exporter update", "risk": "medium", "date": datetime.utcnow() - timedelta(days=25)},
    {"id": f"DEP-{uuid.uuid4().hex[:8]}", "version": "v2.5.0", "title": "Major feature drop (API v2)", "risk": "high", "date": datetime.utcnow() - timedelta(days=18)},
    {"id": f"DEP-{uuid.uuid4().hex[:8]}", "version": "v2.5.1", "title": "Hotfix for API limits", "risk": "critical", "date": datetime.utcnow() - timedelta(days=15)},
    {"id": f"DEP-{uuid.uuid4().hex[:8]}", "version": "v2.6.0", "title": "Dashboard Rewrite", "risk": "high", "date": datetime.utcnow() - timedelta(days=5)},
]

CLUSTERS_CONFIG = [
    {"id": "CL-001", "title": "CSV Export Failure", "severity": "high", "monthly_cost": 45000, "deploy_idx": 1},
    {"id": "CL-002", "title": "Login Session Expiry", "severity": "medium", "monthly_cost": 12000, "deploy_idx": None},
    {"id": "CL-003", "title": "Broken Onboarding Flow", "severity": "critical", "monthly_cost": 85000, "deploy_idx": 2},
    {"id": "CL-004", "title": "Invoice Sync Failure", "severity": "high", "monthly_cost": 60000, "deploy_idx": None},
    {"id": "CL-005", "title": "Mobile App Crashes", "severity": "critical", "monthly_cost": 95000, "deploy_idx": 2},
    {"id": "CL-006", "title": "API Rate Limit Errors", "severity": "medium", "monthly_cost": 22000, "deploy_idx": 3},
    {"id": "CL-007", "title": "Search Index Delays", "severity": "low", "monthly_cost": 5000, "deploy_idx": None},
    {"id": "CL-008", "title": "Dashboard Loading Issues", "severity": "high", "monthly_cost": 55000, "deploy_idx": 4},
    {"id": "CL-009", "title": "Notification Delivery Failure", "severity": "medium", "monthly_cost": 15000, "deploy_idx": None},
    {"id": "CL-010", "title": "Role Permission Bugs", "severity": "critical", "monthly_cost": 72000, "deploy_idx": None},
]

# Provide varied wording per cluster
CLUSTER_WORDS = {
    "CL-001": ["export fails", "cannot download csv", "csv is empty", "timeout on export", "500 error exporting data"],
    "CL-002": ["keeps logging me out", "session expired randomly", "have to login again", "auth token invalid"],
    "CL-003": ["stuck on step 2", "onboarding frozen", "cant complete setup", "getting started page blank"],
    "CL-004": ["invoices not syncing to xero", "qbo sync failed", "missing invoices", "billing integration broken"],
    "CL-005": ["ios app crashes on startup", "android app freezing", "mobile app force closes", "white screen on phone"],
    "CL-006": ["429 too many requests", "rate limit exceeded but we didnt hit it", "api blocked", "quota reached falsely"],
    "CL-007": ["new items not in search", "search results outdated", "delay in search index", "cant find recent record"],
    "CL-008": ["dashboard widgets spinning", "analytics page timeout", "charts not loading", "slow dashboard"],
    "CL-009": ["didnt get email alert", "slack webhook silent", "notifications delayed", "missing push notification"],
    "CL-010": ["admin cant access billing", "permission denied error", "role not updating", "cant invite team member"],
}

# Distribute 5000 tickets across clusters
TICKET_DISTRIBUTION = [0.08, 0.05, 0.12, 0.10, 0.15, 0.09, 0.04, 0.14, 0.08, 0.15] # Sums to 1.0

# ---------------------------------------------------------
# Generation
# ---------------------------------------------------------
def main():
    print("Generating dataset...")
    
    # 1. Generate tickets & map to clusters
    tickets = []
    cluster_tickets = []
    clusters = []
    
    ticket_id_counter = 1
    
    for idx, c_conf in enumerate(CLUSTERS_CONFIG):
        cluster = c_conf.copy()
        cluster["status"] = "open"
        cluster["ticket_count"] = int(NUM_TICKETS * TICKET_DISTRIBUTION[idx])
        cluster["affected_customers"] = int(cluster["ticket_count"] * random.uniform(0.6, 0.9))
        
        c_tickets = []
        for _ in range(cluster["ticket_count"]):
            t_id = ticket_id_counter
            ticket_id_counter += 1
            
            wording = random.choice(CLUSTER_WORDS[cluster["id"]])
            title = f"{wording.capitalize()} - {random.randint(100, 999)}"
            body = f"Customer reported: {wording}. Please investigate."
            
            t = {
                "id": t_id,
                "external_id": f"ZD-{100000 + t_id}",
                "source": random.choice(["zendesk", "intercom", "manual"]),
                "title": title,
                "body": body,
                "customer_id": f"CUST-{random.randint(1000, 20000)}",
                "customer_email": f"user{random.randint(1,90000)}@example.com",
                "severity": cluster["severity"],
                "status": "open",
                "ingested_at": (datetime.utcnow() - timedelta(days=random.randint(1, 30))).isoformat(),
            }
            c_tickets.append(t)
            cluster_tickets.append({"cluster_id": cluster["id"], "ticket_id": t_id, "similarity": round(random.uniform(0.8, 0.99), 4)})
        
        tickets.extend(c_tickets)
        clusters.append(cluster)

    # 2. Investigations (Top 3 clusters: CL-003, CL-005, CL-008)
    inv_targets = [c for c in clusters if c["id"] in ["CL-003", "CL-005", "CL-008"]]
    investigations = []
    evidences = []
    
    for i, inv_c in enumerate(inv_targets):
        inv_id = f"AI-{uuid.uuid4().hex[:6].upper()}"
        dep_id = DEPLOYMENTS[inv_c["deploy_idx"]]["id"] if inv_c["deploy_idx"] is not None else None
        
        inv = {
            "id": inv_id,
            "cluster_id": inv_c["id"],
            "root_cause": f"Issue traced to deployment {DEPLOYMENTS[inv_c['deploy_idx']]['version']} causing {inv_c['title'].lower()}",
            "confidence": round(random.uniform(85, 98), 2),
            "impact_level": inv_c["severity"],
            "affected_customers": inv_c["affected_customers"],
            "revenue_impact_usd": inv_c["monthly_cost"],
            "deploy_correlation_id": dep_id,
            "deploy_correlation_score": round(random.uniform(0.7, 0.95), 4) if dep_id else None,
            "reasoning_steps": [
                "Analyzed 300+ tickets for semantic similarities.",
                f"Found strong correlation with {DEPLOYMENTS[inv_c['deploy_idx']]['version']} release.",
                "Identified error logs matching customer reports.",
                "Synthesized root cause from code changes in the correlated release."
            ],
            "created_at": (datetime.utcnow() - timedelta(days=2)).isoformat()
        }
        investigations.append(inv)
        
        ev_types = ["ticket_pattern", "deploy_correlation", "customer_impact", "similar_ticket"]
        for j, ev_t in enumerate(ev_types):
            evidences.append({
                "id": f"EV-{uuid.uuid4().hex[:6]}",
                "investigation_id": inv_id,
                "evidence_type": ev_t,
                "title": f"Strong signal for {ev_t.replace('_', ' ')}",
                "detail": f"Model detected high confidence signal for {ev_t}.",
                "weight": round(random.uniform(0.5, 0.9), 4),
                "sort_order": j
            })

    # 3. Recommendations
    recommendations = []
    validations = []
    
    for i, inv in enumerate(investigations):
        rec_id = f"REC-{uuid.uuid4().hex[:6].upper()}"
        
        # Make the first one "resolved" so we have a validation loop closure
        status = "resolved" if i == 0 else "open"
        
        rec = {
            "id": rec_id,
            "cluster_id": inv["cluster_id"],
            "investigation_id": inv["id"],
            "title": f"Fix for {inv['root_cause'].split('causing ')[-1]}",
            "description": f"Refactor the module introduced in the correlated deployment to handle edge cases properly.",
            "priority": inv["impact_level"],
            "engineering_effort": random.choice(["low", "medium", "high"]),
            "confidence_score": round(random.uniform(85, 95), 2),
            "status": status,
            "expected_reduction_pct": round(random.uniform(70, 95), 2),
            "expected_recovery_usd": round(inv["revenue_impact_usd"] * random.uniform(0.7, 0.9), 2),
            "jira_title": f"BUG: {inv['root_cause'].split('causing ')[-1].capitalize()}",
            "jira_description": f"Customer reports indicate {inv['root_cause']}",
            "jira_acceptance_criteria": ["Unit tests pass", "Deflection > 80% measured in FixLoop", "No regressions"],
            "created_at": (datetime.utcnow() - timedelta(days=1)).isoformat()
        }
        
        if status == "resolved":
            rec["actual_reduction_pct"] = rec["expected_reduction_pct"] + random.uniform(-5, 5)
            rec["actual_recovery_usd"] = rec["expected_recovery_usd"] + random.uniform(-1000, 1000)
            rec["before_ticket_count"] = 540
            rec["after_ticket_count"] = int(540 * (1 - rec["actual_reduction_pct"]/100))
            
            validations.append({
                "fix_recommendation_id": rec_id,
                "ticket_count": rec["after_ticket_count"],
                "deflection_pct": rec["actual_reduction_pct"],
                "revenue_recovered_usd": rec["actual_recovery_usd"],
                "created_at": datetime.utcnow().isoformat()
            })
            
        recommendations.append(rec)

    # ---------------------------------------------------------
    # Write CSV
    # ---------------------------------------------------------
    print(f"Writing {SEED_DIR}/tickets.csv...")
    with open(f"{SEED_DIR}/tickets.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["external_id", "source", "title", "body", "customer_id", "customer_email", "severity", "status", "ingested_at"])
        writer.writeheader()
        for t in tickets:
            writer.writerow({k: t[k] for k in writer.fieldnames})

    # ---------------------------------------------------------
    # Write SQL
    # ---------------------------------------------------------
    print(f"Writing {SEED_DIR}/seed.sql...")
    with open(f"{SEED_DIR}/seed.sql", "w") as f:
        f.write("-- FixLoop AI Seed Data\n\n")
        
        f.write("-- 1. Deployments\n")
        for d in DEPLOYMENTS:
            f.write(f"INSERT INTO public.deployments (id, version, title, risk, deployed_at) VALUES ('{d['id']}', '{d['version']}', '{d['title']}', '{d['risk']}', '{d['date'].date().isoformat()}');\n")
            
        f.write("\n-- 2. Clusters\n")
        for c in clusters:
            dep_id = DEPLOYMENTS[c["deploy_idx"]]["id"] if c["deploy_idx"] is not None else 'NULL'
            dep_val = f"'{dep_id}'" if dep_id != 'NULL' else 'NULL'
            f.write(f"INSERT INTO public.ticket_clusters (id, title, severity, status, ticket_count, affected_customers, monthly_cost_usd, related_deploy_id) VALUES ('{c['id']}', '{c['title']}', '{c['severity']}', '{c['status']}', {c['ticket_count']}, {c['affected_customers']}, {c['monthly_cost']}, {dep_val});\n")
            
        f.write("\n-- 3. Tickets (Skipping due to size, handled via CSV or JSON, but we can write a few for sanity check if needed. In this script, we'll write the full INSERTs.)\n")
        # Write tickets in chunks to avoid massive memory buffering
        chunk_size = 1000
        for i in range(0, len(tickets), chunk_size):
            chunk = tickets[i:i+chunk_size]
            values = []
            for t in chunk:
                body_safe = t['body'].replace("'", "''")
                title_safe = t['title'].replace("'", "''")
                values.append(f"({t['id']}, '{t['external_id']}', '{t['source']}', '{title_safe}', '{body_safe}', '{t['customer_id']}', '{t['customer_email']}', '{t['severity']}', '{t['status']}', '{t['ingested_at']}')")
            f.write(f"INSERT INTO public.tickets (id, external_id, source, title, body, customer_id, customer_email, severity, status, ingested_at) VALUES {','.join(values)};\n")
            
        f.write("\n-- 4. Cluster Tickets\n")
        for i in range(0, len(cluster_tickets), chunk_size):
            chunk = cluster_tickets[i:i+chunk_size]
            values = [f"('{ct['cluster_id']}', {ct['ticket_id']}, {ct['similarity']})" for ct in chunk]
            f.write(f"INSERT INTO public.cluster_tickets (cluster_id, ticket_id, similarity) VALUES {','.join(values)} ON CONFLICT DO NOTHING;\n")

        f.write("\n-- 5. Investigations\n")
        for inv in investigations:
            dep_val = f"'{inv['deploy_correlation_id']}'" if inv['deploy_correlation_id'] else 'NULL'
            dep_score = inv['deploy_correlation_score'] if inv['deploy_correlation_score'] else 'NULL'
            rs_arr = "ARRAY[" + ",".join([f"'{s.replace(chr(39), chr(39)+chr(39))}'" for s in inv['reasoning_steps']]) + "]"
            f.write(f"INSERT INTO public.investigations (id, cluster_id, root_cause, confidence, impact_level, affected_customers, revenue_impact_usd, deploy_correlation_id, deploy_correlation_score, reasoning_steps, created_at) VALUES ('{inv['id']}', '{inv['cluster_id']}', '{inv['root_cause'].replace(chr(39), chr(39)+chr(39))}', {inv['confidence']}, '{inv['impact_level']}', {inv['affected_customers']}, {inv['revenue_impact_usd']}, {dep_val}, {dep_score}, {rs_arr}, '{inv['created_at']}');\n")
            
        f.write("\n-- 6. Evidence\n")
        for ev in evidences:
            f.write(f"INSERT INTO public.investigation_evidence (id, investigation_id, evidence_type, title, detail, weight, sort_order) VALUES ('{ev['id']}', '{ev['investigation_id']}', '{ev['evidence_type']}', '{ev['title']}', '{ev['detail']}', {ev['weight']}, {ev['sort_order']});\n")
            
        f.write("\n-- 7. Recommendations\n")
        for rec in recommendations:
            f.write(f"INSERT INTO public.fix_recommendations (id, cluster_id, investigation_id, title, description, priority, engineering_effort, confidence_score, status, expected_reduction_pct, expected_recovery_usd, created_at) VALUES ('{rec['id']}', '{rec['cluster_id']}', '{rec['investigation_id']}', '{rec['title'].replace(chr(39), chr(39)+chr(39))}', '{rec['description'].replace(chr(39), chr(39)+chr(39))}', '{rec['priority']}', '{rec['engineering_effort']}', {rec['confidence_score']}, '{rec['status']}', {rec['expected_reduction_pct']}, {rec['expected_recovery_usd']}, '{rec['created_at']}');\n")
            
        f.write("\n-- 8. Validations\n")
        for val in validations:
            f.write(f"INSERT INTO public.validation_results (fix_recommendation_id, ticket_count, deflection_pct, revenue_recovered_usd, created_at) VALUES ('{val['fix_recommendation_id']}', {val['ticket_count']}, {val['deflection_pct']}, {val['revenue_recovered_usd']}, '{val['created_at']}');\n")

        # Sync sequences
        f.write("\n-- 9. Sync Sequences\n")
        f.write("SELECT setval('public.tickets_id_seq', (SELECT MAX(id) FROM public.tickets));\n")


    # ---------------------------------------------------------
    # Write JSON
    # ---------------------------------------------------------
    print(f"Writing {SEED_DIR}/seed.json...")
    with open(f"{SEED_DIR}/seed.json", "w") as f:
        # Convert datetime objects in deployments
        json_deps = []
        for d in DEPLOYMENTS:
            jd = d.copy()
            jd["date"] = jd["date"].isoformat()
            json_deps.append(jd)
            
        json.dump({
            "deployments": json_deps,
            "clusters": clusters,
            "investigations": investigations,
            "recommendations": recommendations,
            "validations": validations
        }, f, indent=2)

    print("Done! Dataset generated successfully.")

if __name__ == "__main__":
    main()

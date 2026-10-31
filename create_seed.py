import random
import hashlib

random.seed(42)

lines = open('seed/seed.sql', 'r', encoding='utf-8').readlines()

# Applications are lines 4 to 100006
app_lines = [l.strip() for l in lines[4:100006] if l.strip()]

approved = [l for l in app_lines if '\tAPPROVED\t' in l][:600]
rejected = [l for l in app_lines if '\tREJECTED\t' in l][:200]
pending = [l for l in app_lines if '\tPENDING\t' in l][:200]

selected = approved + rejected + pending
random.shuffle(selected)

# Load portal users map
portal_map = {}
for line in lines[100008:]:
    parts = line.strip().split('\t')
    if len(parts) == 2 and len(parts[0]) == 10 and len(parts[1]) == 64:
        portal_map[parts[0]] = parts[1]

app_inserts = []
portal_inserts = []
seen_mobiles = set()

for line in selected:
    parts = line.split('\t')
    if len(parts) >= 18:
        app_id = parts[0]
        app_no = parts[1]
        name = parts[2].replace("'", "''")
        mobile = parts[3]
        dob = parts[4]
        gender = parts[5]
        marital = parts[6]
        husband = parts[7].replace("'", "''") if parts[7] != '\\N' else ''
        employer = parts[8].replace("'", "''") if parts[8] != '\\N' else ''
        village = parts[9].replace("'", "''")
        block = parts[10]
        bank_acc = parts[11]
        ifsc = parts[12]
        doc_path = parts[13]
        status = parts[14]
        submitted_at = parts[15]
        decided_at = 'NULL' if parts[16] in ['', '\\N'] else f"'{parts[16]}'"
        decided_by = 'NULL' if parts[17] in ['', '\\N'] else f"'{parts[17]}'"
        
        app_inserts.append(
            f"INSERT INTO applications (id, application_no, applicant_name, mobile, dob, gender, marital_status, husband_name, husband_employer, village, block, bank_account, ifsc, doc_path, status, submitted_at, decided_at, decided_by) "
            f"VALUES ({app_id}, '{app_no}', '{name}', '{mobile}', '{dob}', '{gender}', '{marital}', '{husband}', '{employer}', '{village}', '{block}', '{bank_acc}', '{ifsc}', '{doc_path}', '{status}', '{submitted_at}', {decided_at}, {decided_by}) "
            f"ON CONFLICT (id) DO NOTHING;"
        )
        
        if mobile not in seen_mobiles:
            seen_mobiles.add(mobile)
            pwd_hash = portal_map.get(mobile)
            if not pwd_hash:
                d, mth, y = dob.split('-')[2], dob.split('-')[1], dob.split('-')[0]
                pwd_hash = hashlib.sha256(f"{d}{mth}{y}".encode('utf-8')).hexdigest()
            portal_inserts.append(
                f"INSERT INTO portal_users (mobile, password_hash) VALUES ('{mobile}', '{pwd_hash}') ON CONFLICT (mobile) DO NOTHING;"
            )

with open('app/seed_1k.sql', 'w', encoding='utf-8') as f:
    f.write("-- Sewa Setu 1K citizen seed data (with idempotent inserts)\n\n")
    f.write("-- 1. Applications\n")
    for stmt in app_inserts:
        f.write(stmt + "\n")
    f.write("\n-- 2. Portal Users (for citizen status portal login)\n")
    for stmt in portal_inserts:
        f.write(stmt + "\n")
    f.write("\n-- 3. Reset ID sequence\n")
    f.write("SELECT setval('applications_id_seq', (SELECT MAX(id) FROM applications));\n")

print(f"Created seed_1k.sql with {len(app_inserts)} applications and {len(portal_inserts)} portal users")

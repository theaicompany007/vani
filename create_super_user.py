import os
from pathlib import Path
from dotenv import load_dotenv
import psycopg2

basedir = Path(".")
load_dotenv(basedir / ".env")
load_dotenv(basedir / ".env.local", override=True)

print("=" * 60)
print("Creating Super User...")
print("=" * 60)

conn = psycopg2.connect(os.getenv("SUPABASE_CONNECTION"))
cur = conn.cursor()

# Create/update app_user
print("\n📝 Creating/updating app_user...")
cur.execute("""
    INSERT INTO app_users (supabase_user_id, email, name, is_super_user, is_industry_admin)
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (supabase_user_id) 
    DO UPDATE SET 
        is_super_user = EXCLUDED.is_super_user,
        is_industry_admin = EXCLUDED.is_industry_admin,
        email = EXCLUDED.email
""", ('eb98e4aa-96cc-48d1-ba60-96cc541c4fdf', 'rajvins@theaicompany.co', 'Super Admin', True, True))
conn.commit()
print("✅ User created/updated")

# Get app_user_id
cur.execute("SELECT id FROM app_users WHERE supabase_user_id = %s", ('eb98e4aa-96cc-48d1-ba60-96cc541c4fdf',))
app_user_id = cur.fetchone()[0]
print(f"✅ App User ID: {app_user_id}")

# Grant permissions
print("\n🔑 Granting permissions...")
cur.execute("""
    INSERT INTO user_permissions (user_id, use_case_id, industry_id, granted_by)
    SELECT %s, uc.id, NULL, %s
    FROM use_cases uc
    ON CONFLICT (user_id, use_case_id, industry_id) DO NOTHING
""", (app_user_id, app_user_id))
conn.commit()

# Count permissions
cur.execute("SELECT COUNT(*) FROM user_permissions WHERE user_id = %s", (app_user_id,))
count = cur.fetchone()[0]
print(f"✅ Granted {count} permissions")

cur.close()
conn.close()

print("\n" + "=" * 60)
print("✅ Super User Setup Complete!")
print("=" * 60)
print("Email: rajvins@theaicompany.co")
print(f"User ID: {app_user_id}")
print(f"Permissions: {count} use cases")
print("\n💡 You can now login at: http://localhost:5000/login")
print("=" * 60)


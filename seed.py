"""
Run once: python seed.py
Creates 4 roles + 1 admin user
"""
from database import engine, Base, SessionLocal
from models import User, Role
from auth import hash_password

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# Check if already seeded
if db.query(Role).first():
    print("Already seeded! Delete database.db to start fresh.")
    db.close()
    exit()

# Create 4 roles
roles = {
    "admin": Role(name="admin", permission="full_access"),
    "analyst": Role(name="analyst", permission="upload_edit"),
    "auditor": Role(name="auditor", permission="review"),
    "client": Role(name="client", permission="view"),
}
for role in roles.values():
    db.add(role)
db.commit()

# Refresh to get auto-generated IDs
for role in roles.values():
    db.refresh(role)

# Create admin user with admin role
admin = User(
    email="admin@example.com",
    username="admin",
    hashed_password=hash_password("admin123"),
    role_id=roles["admin"].id,
)
db.add(admin)
db.commit()
db.refresh(admin)
db.close()

print("\n=== Setup Complete ===\n")
print("Admin login:")
print(f"  Email:    admin@example.com")
print(f"  Password: admin123")
print(f"  User ID:  {admin.id}")
print()
print("Roles:")
for name in roles:
    r = db.query(Role).filter(Role.name == name).first()
    print(f"  {name:10s} | permission: {r.permission:12s} | ID: {r.id}")
print()
print("Next: uvicorn main:app --reload")
print("Then: http://localhost:8000/docs")

from database import get_db

conn = get_db()

print(
    "Collect finished matches here"
)

conn.close()

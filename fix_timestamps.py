import sqlite3

c = sqlite3.connect('mediScheme.db')

# Fix ISO-8601 timestamps (with T and Z) to SQLite-compatible format (space separator, no Z)
rows = c.execute("SELECT id, created_at FROM call_reports").fetchall()
for row_id, ts in rows:
    if ts and ('T' in ts or 'Z' in ts):
        fixed = ts.replace('T', ' ').replace('Z', '').split('.')[0]  # strip ms and Z
        c.execute("UPDATE call_reports SET created_at = ? WHERE id = ?", (fixed, row_id))
        print(f"Fixed row {row_id}: {ts} -> {fixed}")

c.commit()
c.close()
print("Done.")

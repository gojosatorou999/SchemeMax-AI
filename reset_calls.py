import sqlite3
c = sqlite3.connect('mediScheme.db')
c.execute("UPDATE call_reports SET matched_scheme_ids='[]'")
c.commit()
print('Reset done')
rows = c.execute("SELECT id, caller_name, matched_scheme_ids FROM call_reports").fetchall()
for r in rows:
    print(r)
c.close()

import sqlite3
import csv
import os

conn = sqlite3.connect('mediScheme.db')
cursor = conn.cursor()

# Get list of tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

if not os.path.exists('data_csv'):
    os.makedirs('data_csv')

for table_name in tables:
    table_name = table_name[0]
    cursor.execute(f'SELECT * FROM {table_name}')
    rows = cursor.fetchall()
    
    if rows:
        # Get column names
        col_names = [description[0] for description in cursor.description]
        
        with open(f'data_csv/{table_name}.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(col_names)
            writer.writerows(rows)
        print(f'Exported {table_name}.csv with {len(rows)} rows')
    else:
        print(f'Skipped {table_name} (empty)')

conn.close()

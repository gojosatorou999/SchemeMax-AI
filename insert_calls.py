import sqlite3, json

conn = sqlite3.connect('mediScheme.db')

records = [
    (
        'CA8415c8941af0026e69afe08eeb0e539b',
        'Vishnu',
        '+919014538043',
        'Name: Vishnu. Age: 23. Location: Hyderabad, Telangana. Monthly income: Rs 2 lakh. Ayushman card: No. Health problem: Heat stroke. Young adult in Hyderabad without health insurance seeking welfare support for acute heat-related illness.',
        json.dumps([]),
        json.dumps({'timestamp':'2026-04-25T08:03:58.882Z','call_sid':'CA8415c8941af0026e69afe08eeb0e539b','phone_number':'+919014538043','name':'Vishnu','age':'23','state':'Hyderabad','monthly_income':'Rs 2 lakh','has_ayushman_card':'No','health_problem':'Heat stroke'}),
        '2026-04-25T08:03:58.882Z'
    ),
    (
        'CA7b7912a0438b51c67d3cf9524ef3049b',
        'Vishnu',
        '+919014538043',
        'Name: Vishnu. Age: 18. Location: Telangana. Monthly income: Rs 2 lakh per year. Ayushman card: No. Health problem: Heart disease. 18-year-old from Telangana with a serious cardiac condition and no Ayushman health card, seeking government health support.',
        json.dumps([]),
        json.dumps({'timestamp':'2026-04-25T08:24:18.005Z','call_sid':'CA7b7912a0438b51c67d3cf9524ef3049b','phone_number':'+919014538043','name':'Vishnu','age':'18','state':'Telangana','monthly_income':'2 lacs','has_ayushman_card':'No','health_problem':'Heart disease'}),
        '2026-04-25T08:24:18.005Z'
    )
]

for r in records:
    conn.execute(
        '''INSERT OR IGNORE INTO call_reports
           (call_id, caller_name, phone, transcript, situation_text, matched_scheme_ids, whatsapp_sent, raw_json, created_at)
           VALUES (?,?,?,?,?,?,0,?,?)''',
        (r[0], r[1], r[2], r[3], r[3], r[4], r[5], r[6])
    )
    print('Inserted', r[0][:30])

conn.commit()
conn.close()
print('Done.')

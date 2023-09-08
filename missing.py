import psycopg2
import re

# Define your PostgreSQL connection parameters
db_params = {
    'dbname': 'new4',
    'user': 'postgres',
    'password': 'manager',
    'host': 'localhost'
}

# Specify the date you want to filter by
date_to_filter = '2023-08-29'

# Connect to the PostgreSQL database
connection = psycopg2.connect(**db_params)
cursor = connection.cursor()

# Define the SQL query
query = """
    SELECT timestamp
FROM uptime_status
WHERE (software_status = '0' OR software_status = '1') 
      AND DATE(timestamp) = '2023-08-29';
"""

# Execute the query with the specified date
cursor.execute(query)

# Fetch all the timestamps
timestamps = cursor.fetchall()
missing_minutes = {}

formatted_timestamps = []

for timestamp_tuple in timestamps:
    formatted_timestamp = timestamp_tuple[0].strftime('%H:%M')
    formatted_timestamps.append(formatted_timestamp)

missing_minutes = {}

for time_str in formatted_timestamps:
    match = re.match(r"(\d+):(\d+)", time_str)
    if match:
        hour, minute = map(int, match.groups())
        for minute_expected in range(minute + 1, 60):
            if f"{hour:02}:{minute_expected:02}" not in formatted_timestamps:
                if hour not in missing_minutes:
                    missing_minutes[hour] = set()  # Use a set instead of a list
                missing_minutes[hour].add(minute_expected)  # Use add() for sets

for hour, minutes in missing_minutes.items():
    print(f"Hour {hour}: Missing Minutes {', '.join(map(str, minutes))}")




    









cursor.close()
connection.close()



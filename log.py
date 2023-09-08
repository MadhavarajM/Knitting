import datetime
import matplotlib.pyplot as plt
import re
from matplotlib.backends.backend_pdf import PdfPages

# Initialize empty lists to store data
timestamps = []
cpu_usage = []
ram_usage = []
revolution_count = []

# Regular expressions for extracting data
cpu_pattern = re.compile(r'CPU: (\d+\.\d+)%')
ram_pattern = re.compile(r'RAM: (\d+) bytes')
revolution_pattern = re.compile(r'REVOLUTION COUNT PER MINUTE: (\d+)')

with open('env\system_stats.log', 'r') as file:
    for line in file:
        parts = line.split(': ')
        if len(parts) >= 4:
            timestamp = datetime.datetime.strptime(parts[0], '%Y-%m-%d %H:%M:%S.%f')

            # Use regular expressions to extract data
            cpu_match = cpu_pattern.search(line)
            ram_match = ram_pattern.search(line)
            revolution_match = revolution_pattern.search(line)

            # Extract the values
            if cpu_match:
                cpu_value = float(cpu_match.group(1))
            else:
                cpu_value = 0.0

            if ram_match:
                ram_value = int(ram_match.group(1))
            else:
                ram_value = 0

            if revolution_match:
                revolutions = int(revolution_match.group(1))
            else:
                revolutions = 0

            timestamps.append(timestamp)
            cpu_usage.append(cpu_value)
            ram_usage.append(ram_value)
            revolution_count.append(revolutions)
        else:
            print(f"Skipping line: {line}")

# Ask the user for the date (format: YYYY-MM-DD)
user_date = input("Enter the date (YYYY-MM-DD): ")

# Filter data for the specified date
filtered_timestamps = [t for t in timestamps if t.date() == datetime.datetime.strptime(user_date, '%Y-%m-%d').date()]
filtered_cpu_usage = [cpu for i, cpu in enumerate(cpu_usage) if timestamps[i].date() == datetime.datetime.strptime(user_date, '%Y-%m-%d').date()]
filtered_ram_usage = [ram for i, ram in enumerate(ram_usage) if timestamps[i].date() == datetime.datetime.strptime(user_date, '%Y-%m-%d').date()]
filtered_revolution_count = [rev for i, rev in enumerate(revolution_count) if timestamps[i].date() == datetime.datetime.strptime(user_date, '%Y-%m-%d').date()]

print(filtered_timestamps)
# Extract hours for grouping
hours = [t.hour for t in filtered_timestamps]
print(hours)

# Initialize dictionaries to store hourly sums
hourly_cpu_sum = {}
hourly_ram_sum = {}
hourly_revolution_sum = {}

# Calculate hourly sums
for hour, cpu, ram, revolution in zip(hours, filtered_cpu_usage, filtered_ram_usage, filtered_revolution_count):
    if hour not in hourly_cpu_sum:
        hourly_cpu_sum[hour] = 0
        hourly_ram_sum[hour] = 0
        hourly_revolution_sum[hour] = 0
    hourly_cpu_sum[hour] += cpu
    hourly_ram_sum[hour] += ram
    hourly_revolution_sum[hour] += revolution

total_ram = 16 * 1024 * 1024 * 1024  # Total RAM in bytes (16 GB)

# Calculate RAM usage as a percentage of total RAM and update the hourly_ram_sum dictionary
for hour, ram in hourly_ram_sum.items():
    ram_percentage = (ram / total_ram) * 100
    hourly_ram_sum[hour] = ram_percentage

# Calculate percentage of RAM used based on RAM usage percentage
for hour, ram_percentage in hourly_ram_sum.items():
    ram_used_percentage = 100 - ram_percentage/100
    hourly_ram_sum[hour] = ram_used_percentage

# Create a PDF file to save the plots
pdf_pages = PdfPages(f'system_stats_{user_date}.pdf')

# Plot CPU Usage by Hour
plt.figure(figsize=(12, 6))
plt.bar(hourly_cpu_sum.keys(), hourly_cpu_sum.values())
plt.xlabel('Hour of the Day')
plt.ylabel('Total CPU Usage (%)')
plt.title(f'Total CPU Usage by Hour for {user_date}')
plt.xticks(list(hourly_cpu_sum.keys()))

# Add annotation for CPU usage percentage
for hour, cpu_percentage in hourly_cpu_sum.items():
    plt.annotate(f'{cpu_percentage:.2f}%', (hour, cpu_percentage), textcoords="offset points", xytext=(0, 10), ha='center',fontsize = 6)

pdf_pages.savefig()  # Save this plot to the PDF file

# Plot RAM Usage by Hour
plt.figure(figsize=(12, 6))
plt.bar(hourly_ram_sum.keys(), hourly_ram_sum.values())
plt.xlabel('Hour of the Day')
plt.ylabel('Total RAM Used (%)')
plt.title(f'Total RAM Usage by Hour for {user_date}')
plt.xticks(list(hourly_ram_sum.keys()))

# Add annotation for RAM used percentage
for hour, ram_used_percentage in hourly_ram_sum.items():
    plt.annotate(f'{ram_used_percentage:.2f}%', (hour, ram_used_percentage), textcoords="offset points", xytext=(0, 10), ha='center',fontsize = 6)

pdf_pages.savefig()  # Save this plot to the PDF file

# Plot Revolution Count by Hour
plt.figure(figsize=(12, 6))
plt.bar(hourly_revolution_sum.keys(), hourly_revolution_sum.values())
plt.xlabel('Hour of the Day')
plt.ylabel('Total Revolution Count')
plt.title(f'Total Revolution Count by Hour for {user_date}')
plt.xticks(list(hourly_revolution_sum.keys()))

# Add annotation for Revolution Count
for hour, revolution_count in hourly_revolution_sum.items():
    plt.annotate(f'{revolution_count}', (hour, revolution_count), textcoords="offset points", xytext=(0, 9), ha='center',fontsize = 6)

pdf_pages.savefig()  # Save this plot to the PDF file

pdf_pages.close()  



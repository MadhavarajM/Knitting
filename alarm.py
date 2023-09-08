import psycopg2
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import datetime
from io import BytesIO
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.cm as cm
def generate_plots_pdf(start_date, end_date):
    # Connect to the database
    conn = psycopg2.connect(host="localhost", database="new", user="postgres", password="manager")
    cursor = conn.cursor()
    # Convert the date strings to datetime objects
    start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
    end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
    # Calculate the number of days in the date range
    num_days = (end_date - start_date).days + 1
    # Create a PDF file to save the plots
    pdf_buffer = BytesIO()
    pdf_pages = PdfPages(pdf_buffer)
    plt.ioff()
    # Iterate over the date range
    for i in range(num_days):
        # Calculate the current date within the range
        current_date = start_date + datetime.timedelta(days=i)
        # Create a new figure and subplots for each date
        fig, ax1 = plt.subplots(figsize=(10, 6))
        cursor.execute('''
            SELECT DATE(timestamp) AS date,
                   EXTRACT(HOUR FROM timestamp) AS hour,
                   COUNT(*) AS rotation_count
            FROM rotation_details
            WHERE timestamp >= %s AND timestamp < %s + interval '1 day'
            GROUP BY date, hour
            ORDER BY date, hour;
        ''', (current_date, current_date))
        data1 = cursor.fetchall()
        # Extract the data from the query results
        dates1 = [row[0] for row in data1]
        hours1 = [row[1] for row in data1]
        rotation_counts1 = [row[2] for row in data1]
        # Plot the first query
        # Plot the first query as a bar graph
        ax1.bar(hours1, rotation_counts1, label='Rotation Count', color='red')
        ax1.set_xlabel('Time of the Day(HOUR)')
        ax1.set_ylabel('Rotation Count')
        ax1.set_title(f'Rotation Count by Hour - {current_date}')
        ax1.set_xticks(range(24))
        ax1.legend()
        for i, count in enumerate(rotation_counts1):
            ax1.annotate(str(count), xy=(hours1[i], count), xytext=(hours1[i], count + 10),
                 ha='center', va='bottom', fontsize=8, color='black')
        pdf_pages.savefig(fig)
        # Close the current figure to move to the next plot
        plt.close(fig)
        cursor.execute('''
    SELECT 
        DATE(dd.timestamp) AS date,
        EXTRACT(HOUR FROM dd.timestamp) AS hour,
        dt.defect_name AS defect_type,
        COUNT(*) AS alarm_count
    FROM defect_details dd
    JOIN alarm_status AS a ON a.defect_id = dd.defect_id
    JOIN defect_type AS dt ON dd.defecttyp_id = dt.defecttyp_id
    WHERE dd.timestamp >= %s AND dd.timestamp < %s + interval '1 day'
    GROUP BY date, hour, defect_type, dt.defecttyp_id, dt.defect_name
    ORDER BY date, hour;
''',(current_date, current_date))
        data6 = cursor.fetchall() 
        unique_dates = list(set(row[0] for row in data6))
        for date in unique_dates:
            fig, ax = plt.subplots(figsize=(20, 6))
            plt.title(f'Alarm Counts per Hour for Defect Types on {date}') 
            filtered_data = [row for row in data6 if row[0] == date]

            hours = [row[1] for row in filtered_data]
            defect_types = [row[2] for row in filtered_data]
            alarm_counts = [row[3] for row in filtered_data]
            unique_defect_types = list(set(defect_types))
                    
            stacked_data = {defect_type: [] for defect_type in unique_defect_types}
            
            for i, defect_type in enumerate(unique_defect_types):
                counts = [alarm_count for j, alarm_count in enumerate(alarm_counts) if defect_types[j] == defect_type]
                hours_for_defect = [hour for j, hour in enumerate(hours) if defect_types[j] == defect_type] 
                stacked_data[defect_type] = counts
            
            defect_type_colors = {
                    'oil': 'red',
                    'twoply': 'green',
                    'lycra': 'blue',
                    "needln" : 'orange',
                    'count_mix' : 'yellow',
                    'hole' : 'brown',
                    'shut_off' : 'violet'
                }
            defect_type_legend = {}
            for defect_type, counts in stacked_data.items():
                color = defect_type_colors.get(defect_type, 'gray')
                defect_type_legend[defect_type] = color
                for i, count in enumerate(counts):
                    hours_for_defect = [hour for i, hour in enumerate(hours) if defect_types[i] == defect_type]
                    ax.bar(hours_for_defect[i], count, label=defect_type, color=color)
            ax.set_xlabel('Hour of the Day')
            ax.set_ylabel('Alarm Count')
            ax.set_xticks(range(24))  # Set x-axis ticks to cover 24 hours
            ax.set_xticklabels([f'{hour}' for hour in range(24)])
            legend_labels = list(defect_type_legend.keys())
            legend_colors = list(defect_type_legend.values())
            legend_handles = [plt.Line2D([0], [0], color=color, label=label) for label, color in defect_type_legend.items()]
            ax.legend(handles=legend_handles, labels=legend_labels)
            pdf_pages.savefig(fig)
            plt.close(fig)
    pdf_pages.close()
    # Close the cursor and database connection
    cursor.close()
    conn.close()
    # Reset the buffer position and return the PDF buffer
    pdf_buffer.seek(0)
    return pdf_buffer

#@app.route('/generate_pdf', methods=['POST'])
def generate_pdf(report_date):
    
    # Generate the filename using the provided report_date
    filename = f"KPR_PERFORMANCE_REPORT_{report_date}.pdf"
    pdf_buffer = generate_plots_pdf(report_date, report_date)  # Assuming generate_plots_pdf uses the provided report_date
    # Write the PDF buffer contents to a local file
    with open(filename, 'wb') as f:
        f.write(pdf_buffer.getvalue())
if __name__ == '__main__':
    # Get the date from the user
    user_input = input("Enter the report date (YYYY-MM-DD): ")
    try:
        generate_pdf(user_input)
        print(f"PDF generated for {user_input}")
    except ValueError:
        print("Invalid date format. Please use YYYY-MM-DD format.")
        raise





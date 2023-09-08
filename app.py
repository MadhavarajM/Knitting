import psycopg2
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import numpy as np
import datetime
from io import BytesIO
from flask import Flask, render_template, request, make_response, send_file
from matplotlib.backends.backend_pdf import PdfPages
import pandas as pd
import matplotlib.dates as mdates
import matplotlib.image as mpimg
app = Flask(__name__)
def round_to_nearest_multiple_of_3(x):
    rounded_value = int(3 * round(float(x) / 3))
    if rounded_value <= 30:
        return rounded_value
    else:
        return 30
def generate_plots_pdf(start_date, end_date):
    # Connect to the database
    conn = psycopg2.connect(host="localhost", database="new4", user="postgres", password="manager")
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
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(21, 29.7))
        plt.subplots_adjust(hspace=0.8)
        fig.suptitle(f"SCM PRODUCTION REPORT - {current_date}", fontsize=24, y=0.93, x=0.52)
        logo_path = 'logo.jpeg'
        logo_img = mpimg.imread(logo_path)
        ax_logo = fig.add_subplot(1, 1, 1)
        # Adjust the logo's position (move it up or down)
        logo_y_position = 0.87  # Adjust this value (0.7 is the default)
        ax_logo.set_position([0.68, logo_y_position, 0.2, 0.2])  # [left, bottom, width, height]
        # Adjust the logo's size
        logo_width = 0.2  # Adjust this value (0.2 is the default)
        ax_logo.imshow(logo_img, extent=[0, logo_width, 0, logo_width * logo_img.shape[0] / logo_img.shape[1]])
        # Turn off axis for the logo subplot
        ax_logo.axis('off')
        ax_logo.set_frame_on(False) 
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
        ax1.set_xlabel('Time of the Day(HOUR)', fontsize = 16)
        ax1.set_ylabel('Rotation Count', fontsize = 16)
        ax1.set_title(f'Rotation Count by Hour - {current_date}', fontsize = 16)
        ax1.set_xticks(range(24))
        ax1.legend()
        for i, count in enumerate(rotation_counts1):
            ax1.annotate(str(count), xy=(hours1[i], count), xytext=(hours1[i], count + 10),
                 ha='center', va='bottom', fontsize=8, color='black')
        # Execute the second query to fetch data
        cursor.execute('''
            SELECT DATE(timestamp) AS date,
                   EXTRACT(HOUR FROM timestamp) AS hour,
                   COUNT(*) AS defect_count
            FROM defect_details
            WHERE timestamp >= %s AND timestamp < %s + interval '1 day'
            GROUP BY date, hour
            ORDER BY date, hour;
        ''', (current_date, current_date))
        data2 = cursor.fetchall()
        # Extract the data from the query results
        dates2 = [row[0] for row in data2]
        hours2 = [row[1] for row in data2]
        defect_counts2 = [row[2] for row in data2]
        # Plot the second query
       # Plot the second query as a bar graph
        ax2.bar(hours2, defect_counts2, label='Defect Count', color='blue')
        ax2.set_xlabel('Time of the Day(Hour)')
        ax2.set_ylabel('Defect Count')
        ax2.set_title(f'Defect Count by Hour - {current_date}')
        ax2.set_xticks(range(24))
        ax2.legend()
        for i, count in enumerate(defect_counts2):
    # Calculate the position of the text slightly above the bar
            annotation_y = count + 2 if count + 2 < ax2.get_ylim()[1] else count - 2
            ax2.annotate(str(count), xy=(hours2[i], count), xytext=(hours2[i], annotation_y),
                        ha='center', va='bottom', fontsize=8, color='black')
        # Execute the third query to fetch data for defect counts by type
        cursor.execute('''
            SELECT dt.defect_name,
                   COALESCE(COUNT(*), 0) AS defect_count
            FROM defect_details d
            JOIN defect_type dt ON d.defecttyp_id = dt.defecttyp_id
            WHERE DATE(d.timestamp) = %s
            GROUP BY dt.defect_name
            ORDER BY defect_count DESC;
        ''', (current_date,))
        data3 = cursor.fetchall()
        # Extract the data from the third query results
        defect_names3 = [row[0] for row in data3]
        defect_counts3 = [row[1] for row in data3]
        # Plot the third query
        ax3.bar(defect_names3, defect_counts3)
        ax3.set_xlabel('Defect Type')
        ax3.set_ylabel('Defect Count')
        ax3.set_title(f'Defect Count by Type - {current_date}')
        ax3.set_xticks(np.arange(len(defect_names3)))
        ax3.set_xticklabels(defect_names3, rotation=45, ha='right')
        # Save the current plot to the PDF file
        pdf_pages.savefig(fig)
        # Close the current figure to move to the next plot
        plt.close(fig)
        
        query = '''
            SELECT
                roll_number,
                timestamp AS roll_start_date,
                order_no,
                shift_no
            FROM roll_details
            WHERE DATE_TRUNC('day', timestamp) = %s::date
            ORDER BY timestamp DESC;
        '''
        cursor.execute(query, (current_date,))
        data = cursor.fetchall()

        # Transform data into a list of lists for the roll details table
        roll_details_cellText = [
            [str(row[0]), row[1], 'null' if row[2] is None else str(row[2]), 'null' if row[3] is None else str(row[3])]
            for row in data
        ]

        roll_details_columns = ['Roll Number', 'Roll Start Date', 'Order No', 'Shift No']

        fig, ax4 = plt.subplots(figsize=(21, 29.7))
        ax_logo = fig.add_subplot(1, 1, 1)
        ax_logo.imshow(logo_img)
        ax_logo.axis('off')
        logo_y_position = 0.83  # Adjust this value (0.7 is the default)
        ax_logo.set_position([0.68, logo_y_position, 0.2, 0.2])  # [left, bottom, width, height]
        # Adjust the logo's size
        logo_width = 0.2  # Adjust this value (0.2 is the default)
        ax_logo.imshow(logo_img, extent=[0, logo_width, 0, logo_width * logo_img.shape[0] / logo_img.shape[1]])
        # Turn off axis for the logo subplot
        ax_logo.axis('off')
        ax_logo.set_frame_on(False)
        ax4.axis('tight')
        ax4.axis('off')
        ax4.table(cellText=[roll_details_columns] + roll_details_cellText, loc='center',bbox=[0.1, 0.3, 0.8, 0.5])
        ax4.set_title(f'Roll Details for {current_date.strftime("%Y-%m-%d")}')
        pdf_pages.savefig(fig)
        plt.close(fig)

        # Execute the query to retrieve defect log data
        cursor.execute('''
            SELECT 
                dd.timestamp AS timestamp,
                dt.defect_name AS defect_type
            FROM defect_details dd
            JOIN alarm_status AS a ON a.defect_id = dd.defect_id
            JOIN defect_type AS dt ON dd.defecttyp_id = dt.defecttyp_id
            WHERE dd.timestamp >= %s AND dd.timestamp < %s + interval '1 day'
            ORDER BY dd.timestamp;
        ''', (current_date, current_date))
        data6 = cursor.fetchall()

        defect_log_df = pd.DataFrame(data6, columns=['timestamp', 'defect_type'])
        defect_log_df['date'] = defect_log_df['timestamp'].dt.date
        defect_log_df['time'] = defect_log_df['timestamp'].dt.strftime('%H:%M:%S')  # Format the time as HH:MM:SS
        defect_log_df.drop(columns=['timestamp'], inplace=True)
        defect_log_table_data = []
        

        for sno, row in enumerate(defect_log_df.iterrows(), start=1):
            defect_log_table_data.append([sno, row[1]['time'], row[1]['defect_type']])

        
        rows_per_page = 65
        num_pages = -(-len(defect_log_table_data) // rows_per_page)
        for page_num in range(num_pages):
            start_idx = page_num * rows_per_page
            end_idx = (page_num + 1) * rows_per_page
            defect_log_table_data_page = defect_log_table_data[start_idx:end_idx]

            # Create a new page for each set of data
            fig, ax5 = plt.subplots(figsize=(21, 29.7))
            ax_logo = fig.add_subplot(1, 1, 1)
            ax_logo.imshow(logo_img)
            ax_logo.axis('off')
            logo_y_position = 0.83  # Adjust this value (0.7 is the default)
            ax_logo.set_position([0.68, logo_y_position, 0.2, 0.2])  # [left, bottom, width, height]
            # Adjust the logo's size
            logo_width = 0.2  # Adjust this value (0.2 is the default)
            ax_logo.imshow(logo_img, extent=[0, logo_width, 0, logo_width * logo_img.shape[0] / logo_img.shape[1]])
            # Turn off axis for the logo subplot
            ax_logo.axis('off')
            ax_logo.set_frame_on(False)
            ax5.set_title(f"Defect Log Report {current_date}", fontsize=24)
            ax5.axis('off')

            # Calculate the position and size of the table based on the title size and available space
            title_height = 0.1  # Adjust this value based on the title height
            table_height = 1.0  # Adjust this value based on the desired table height
            table_bottom = 1 - title_height - table_height  # Calculate the bottom position of the table
            table = ax5.table(
                cellText=defect_log_table_data_page,
                colLabels=['SNo', 'Time', 'Defect Type'],
                cellLoc='center',
                loc='center',
                bbox=[0.1, table_bottom, 0.8, table_height]
            )
            table.auto_set_font_size(False)
            table.set_fontsize(20)
            table.auto_set_column_width([5, 5, 5])
            table.scale(1, 2)
        
            pdf_pages.savefig(fig)
            plt.close(fig)
        cursor.execute('''
                            SELECT DATE_TRUNC('minute', timestamp) AS minute_start,
                                    DATE_TRUNC('minute', timestamp) + INTERVAL '1 minute' AS minute_end,
                                    COUNT(rotation) AS rotation_count,
                                    TO_CHAR(DATE_TRUNC('minute', timestamp), 'YYYY-MM-DD') AS day
                            FROM rotation_details
                            WHERE timestamp >= %s AND timestamp < %s + INTERVAL '1 day'
                            GROUP BY minute_start, minute_end, day
                            ORDER BY day, minute_start;
    ''', (current_date, current_date))
        data5 = cursor.fetchall()
        df = pd.DataFrame(data5, columns=['minute_start', 'minute_end', 'rotation_count', 'day'])
        df['rotation_count'] = df['rotation_count'].apply(round_to_nearest_multiple_of_3)
        # Get the unique dates in the DataFrame
        unique_dates = df['day'].unique()
        # Create a dictionary to hold the RPM Count for each minute in an hour for each day
        minute_rpm_counts = {date: {hour: {minute: 0 for minute in range(60)} for hour in range(24)} for date in unique_dates}
        # Populate the RPM Count in the dictionary based on the data in the DataFrame
        for _, row in df.iterrows():
            date = row['day']
            hour = row['minute_start'].hour
            minute = row['minute_start'].minute
            rpm_count = row['rotation_count']
            minute_rpm_counts[date][hour][minute] = rpm_count
        # Create lists for plotting
        hours = list(range(24))
        minutes = list(range(60))
        rpm_counts = [minute_rpm_counts[date][hour][minute] for date in unique_dates for hour in range(24) for minute in range(60)]
        # Create a list of datetime objects for the x-axis (for proper formatting)
        datetime_labels = [pd.to_datetime(f'{date} {hour:02d}:{minute:02d}') for date in unique_dates for hour in range(24) for minute in range(60)]
        fig, ax = plt.subplots(figsize=(25, 10))
        ax_logo = fig.add_subplot(1, 1, 1)
        ax_logo.imshow(logo_img)
        ax_logo.axis('off')
        logo_y_position = 0.83  # Adjust this value (0.7 is the default)
        ax_logo.set_position([0.68, logo_y_position, 0.2, 0.2])  # [left, bottom, width, height]
        # Adjust the logo's size
        logo_width = 0.2  # Adjust this value (0.2 is the default)
        ax_logo.imshow(logo_img, extent=[0, logo_width, 0, logo_width * logo_img.shape[0] / logo_img.shape[1]])
        # Turn off axis for the logo subplot
        ax_logo.axis('off')
        ax_logo.set_frame_on(False)
        ax.plot(datetime_labels, rpm_counts, marker='o', linestyle='None', color='blue')
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax.set_xlabel('Time of the day (Hour)')
        ax.set_ylabel('Rotation Per Minute (RPM)')
        ax.set_title(f'RPM Count for {current_date.strftime("%Y-%m-%d")}')
        pdf_pages.savefig(fig)
        # Close the current figure to move to the next plot
        plt.close(fig)
    # Close the PDF file
    pdf_pages.close()
    # Close the cursor and database connection
    cursor.close()
    conn.close()
    # Reset the buffer position and return the PDF buffer
    pdf_buffer.seek(0)
    return pdf_buffer
@app.route('/')
def index():
    return render_template('index.html')
@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    start_date = request.form['start_date']
    end_date = request.form['end_date']
    # Call the function to generate the PDF
    pdf_buffer = generate_plots_pdf(start_date, end_date)
    # Set the appropriate headers for PDF download
    # Check if start date and end date are the same
    if start_date == end_date:
        # If they are the same, use only the start date in the filename
        filename = f"SCM_PERFORMANCE_REPORT_{start_date}.pdf"
    else:
        # If they are different, use both start date and end date in the filename
        filename = f"SCM_PERFORMANCE_REPORT_{start_date}_TO_{end_date}.pdf"
    response = make_response(pdf_buffer)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return response
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

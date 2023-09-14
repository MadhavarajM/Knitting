import psycopg2
import matplotlib.pyplot as plt
import matplotlib
#matplotlib.use('Agg')
import numpy as np
import datetime
from io import BytesIO
from matplotlib.backends.backend_pdf import PdfPages
import pandas as pd
from collections import Counter
import matplotlib.dates as mdates
import matplotlib.image as mpimg
import locale

locale.setlocale(locale.LC_TIME, 'C')
encoding = 'utf-8'
def round_to_nearest_multiple_of_3(x):
    rounded_value = int(3 * round(float(x) / 3))
    if rounded_value <= 30:
        return rounded_value
    else:
        return 30
def generate_plots_pdf(start_date, end_date):
    # Connect to the database
    conn = psycopg2.connect(host="localhost", database="new8", user="postgres", password="manager")
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
        if not data6:
            pdf_pages.close()  # Check if there is no data
            return pdf_buffer, False  
        else:
            fig, (ax1, ax2 , ax3) = plt.subplots(3, 1, figsize=(21, 29.7))
            plt.subplots_adjust(hspace=0.8)
            logo_path = 'env/logo.jpeg'
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
            #print(data1)
            # Extract the data from the query results
            dates1 = [row[0] for row in data1]
            hours1 = [row[1] for row in data1]
            rotation_counts1 = [row[2] for row in data1]
            # Plot the first query
            # Plot the first query as a bar graph
            ax1.bar(hours1, rotation_counts1, label='Rotation Count', color='red')
            ax1.set_xlabel('Time of the Day(HOUR)',fontsize=18)
            ax1.set_ylabel('Rotation Count',fontsize=18)
            ax1.set_title('PRODUCTION REPORT',fontsize=24 , y=1.03)
            ax1.set_xticks(range(24))
            ax1.legend()
            text_x = 0.85
            text_y = max(rotation_counts1) + 600  # Adjust the y-coordinate as needed
            ax1.text(text_x, text_y, f"Date: {current_date}", fontsize=28, color='black')
            for i, count in enumerate(rotation_counts1):
                ax1.annotate(str(count), xy=(hours1[i], count), xytext=(hours1[i], count + 10),
                    ha='center', va='bottom', fontsize=15, color='black' )
                

            defect_log_df = pd.DataFrame(data6, columns=['timestamp', 'defect_type'])
            defect_log_df['date'] = defect_log_df['timestamp'].dt.date
            defect_log_df['time'] = defect_log_df['timestamp'].dt.strftime('%H:%M:%S')  # Format the time as HH:MM:SS
            defect_log_df.drop(columns=['timestamp'], inplace=True)
            defect_log_table_data = []
            

            for sno, row in enumerate(defect_log_df.iterrows(), start=1):
                defect_log_table_data.append([sno, row[1]['time'], row[1]['defect_type']])
            
            

            hour_counts = Counter(item[1].split(':')[0] for item in defect_log_table_data)
            hours = [str(i).zfill(2) for i in range(24)]  # Generate a list of all 24 hours as strings
            counts = [hour_counts[hour] for hour in hours]
            ax2.bar(hours, counts)
            ax2.set_xlabel('Time of the Day(Hour)',fontsize=18)
            ax2.set_ylabel('Defect Count',fontsize=18)
            ax2.set_title("DEFECT REPORT", fontsize=24 , y = 1.03)
            ax2.set_xticks(hours)
            for hour, count in zip(hours, counts):
              ax2.text(hour, count, str(count), ha='center', va='bottom', fontsize=15)
           
 
            defect_type_counts = Counter(item[2] for item in defect_log_table_data)
            defect_types = list(defect_type_counts.keys())
            defect_counts = list(defect_type_counts.values())
            ax3.bar(defect_types, defect_counts)
            ax3.set_xlabel('Defect Type',fontsize=18)
            ax3.set_ylabel('Defect Count',fontsize=18)
            ax3.set_title("DEFECT COUNT BY TYPE", fontsize=24)
            for i, count in enumerate(defect_counts):
               ax3.text(i, count, str(count), ha='center', va='bottom', fontsize=20)

            pdf_pages.savefig(fig)
            plt.close(fig)
            

            query = '''
    SELECT
        roll_number,
        DATE(timestamp) AS roll_start_date,
        EXTRACT(HOUR FROM timestamp)||':'||EXTRACT(MINUTE FROM timestamp)||':'||EXTRACT(SECOND FROM timestamp) AS roll_start_time,
        order_no
    FROM roll_details
    WHERE DATE_TRUNC('day', timestamp) = %s::date
    ORDER BY timestamp DESC;
'''

            cursor.execute(query, (current_date,))
            data = cursor.fetchall()
            #print(data)

            roll_details_cellText = [
                [str(row[0]), str(row[1]), row[2], 'null' if row[3] is None else str(row[3])]
                for row in data
            ]
            

            roll_details_df = pd.DataFrame(roll_details_cellText, columns=['Roll Number', 'Roll Start Date', 'Roll Start Time', 'Order No'])
            #print(roll_details_df['Roll Start Time'])
            roll_details_df['Roll Start Time'] = pd.to_datetime(roll_details_df['Roll Start Time'], format="%H:%M:%S.%f",errors='coerce',exact=False,infer_datetime_format=True)
            roll_details_df['Roll Start Time'] = roll_details_df['Roll Start Time'].dt.strftime('%H:%M:%S')
            roll_details_df = roll_details_df.dropna(subset=['Roll Start Time'])
            #print(roll_details_df)
            roll_details_df = roll_details_df.sort_values(by='Roll Start Time', ascending=True)
            roll_details_df = roll_details_df.reset_index(drop=True)
            #print(roll_details_df)
            defect_counts = []
            for index, row in roll_details_df.iterrows():
                #print("hi")
                roll_start_time = pd.Timestamp(row['Roll Start Time'])  
                # Access the "Roll Start Time" of the next row
                next_row_index = index + 1
                if next_row_index < len(roll_details_df):
                    Roll_End_Time = pd.Timestamp(roll_details_df.at[next_row_index, 'Roll Start Time'])
                else:
                    Roll_End_Time = roll_start_time + pd.DateOffset(days=1)
                defect_count = {}  # Use a dictionary to store defect counts
                for defect_type in defect_log_df['defect_type']:
                    defect_count[defect_type] = 0  # Initialize counts for all defect types
                for j in range(i + 1, len(defect_log_df)):
                    log_time = pd.Timestamp(defect_log_df.at[j, 'time'])   
                    # If log_time is within the time range, increment the corresponding defect count
                    if roll_start_time <= log_time <= Roll_End_Time:
                        defect_type = defect_log_df.at[j, 'defect_type']
                        defect_count[defect_type] += 1
                defect_counts.append(defect_count)
            # Add defect_counts as a new column to roll_details_df
            roll_details_df['Defect Counts'] = defect_counts
           
            
            fig, ax5 = plt.subplots(figsize=(21, 10))
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
            ax5.set_title(f"Roll Details", fontsize=24)
            ax5.axis('tight')
            ax5.axis('off')
            for index, row in roll_details_df.iterrows():
                defect_count = row['Defect Counts']
                formatted_defect_count = ', '.join([f'{defect_type}: {count}' for defect_type, count in defect_count.items()])
                roll_details_df.at[index, 'Defect Counts'] = formatted_defect_count

            # Convert the DataFrame to a list
            table_data = roll_details_df.values.tolist()

            # Create the table with the formatted data
            ax5.table(cellText=table_data, colLabels=['Roll Number', 'Roll Start Date', 'Roll End Time', 'Order No', 'Defect Count'], loc='center', bbox=[0.03, 0.3, 0.9, 0.5], fontsize=25)
            pdf_pages.savefig(fig)
            plt.close(fig)

            rows_per_page = 65
            num_pages = -(-len(defect_log_table_data) // rows_per_page)
            for page_num in range(num_pages):
                start_idx = page_num * rows_per_page
                end_idx = (page_num + 1) * rows_per_page
                defect_log_table_data_page = defect_log_table_data[start_idx:end_idx]

                # Create a new page for each set of data
                fig, ax4 = plt.subplots(figsize=(21, 29.7))
                ax_logo = fig.add_subplot(1, 1, 1)
                ax_logo.imshow(logo_img)
                ax_logo.axis('off')
                logo_y_position = 0.87  # Adjust this value (0.7 is the default)
                ax_logo.set_position([0.68, logo_y_position, 0.2, 0.2])  # [left, bottom, width, height]
                # Adjust the logo's size
                logo_width = 0.2  # Adjust this value (0.2 is the default)
                ax_logo.imshow(logo_img, extent=[0, logo_width, 0, logo_width * logo_img.shape[0] / logo_img.shape[1]])
                # Turn off axis for the logo subplot
                ax_logo.axis('off')
                ax_logo.set_frame_on(False)
                ax4.set_title(f"Defect Log Report", fontsize=24)
                ax4.axis('off')

                # Calculate the position and size of the table based on the title size and available space
                title_height = 0.1  # Adjust this value based on the title height
                table_height = 1.0  # Adjust this value based on the desired table height
                table_bottom = 1 - title_height - table_height  # Calculate the bottom position of the table
                table = ax4.table(
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
            # Close the current figure to move to the next plot
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
            fig, ax = plt.subplots(figsize=(30, 10))
            ax_logo = fig.add_subplot(1, 1, 1)
            ax_logo.imshow(logo_img)
            ax_logo.axis('off')
            logo_y_position = 0.89  # Adjust this value (0.7 is the default)
            ax_logo.set_position([0.68, logo_y_position, 0.1, 0.1])  # [left, bottom, width, height]
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
            return pdf_buffer, True

def generate_pdf_performance(report_date):
    filename = f"SCM_PERFORMANCE_REPORT_{report_date}.pdf"
    pdf_buffer, has_data = generate_plots_pdf(report_date, report_date)
    
    if has_data:
        with open(filename, 'wb') as f:
            f.write(pdf_buffer.getvalue())
        print(f"PDF generated for {report_date}")
    else:
        print(f"No data found for {report_date}. PDF not generated.")

# Run the scheduled tasks
if __name__ == '__main__':
   user_input = input("Enter the report date (YYYY-MM-DD): ")
   try:
        generate_pdf_performance(user_input)
   except ValueError:
        print("Invalid date format. Please use YYYY-MM-DD format.")

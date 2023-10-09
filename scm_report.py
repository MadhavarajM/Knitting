import psycopg2
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import numpy as np
import datetime
from datetime import timedelta
from io import BytesIO
from matplotlib.backends.backend_pdf import PdfPages
import pandas as pd
from collections import Counter
import matplotlib.dates as mdates
import matplotlib.image as mpimg
import locale

locale.setlocale(locale.LC_TIME, 'C')
encoding = 'utf-8'

def generate_plots_pdf(start_date, end_date):
    # Connect to the database
    conn = psycopg2.connect(host="localhost", database="new11", user="postgres", password="manager")
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
            fig, (ax, ax1 , ax2) = plt.subplots(3, 1, figsize=(21, 29.7))
            plt.subplots_adjust(hspace=0.8)
            logo_path = 'env\logo.jpeg'
            logo_img = mpimg.imread(logo_path)
            ax_logo = fig.add_subplot(1, 1, 1)
            # Adjust the logo's position (move it up or down)
            logo_y_position = 0.87  # Adjust this value (0.7 is the default)
            ax_logo.set_position([0.68, logo_y_position, 0.2, 0.2]) 
            # Adjust the logo's size
            logo_width = 0.2  # Adjust this value (0.2 is the default)
            ax_logo.imshow(logo_img, extent=[0, logo_width, 0, logo_width * logo_img.shape[0] / logo_img.shape[1]])
            # Turn off axis for the logo subplot
            ax_logo.axis('off')
            ax_logo.set_frame_on(False)
            logo_path_2 = 'env\scm-garments.jpg'
            logo_img = mpimg.imread(logo_path_2)
            ax_logo = fig.add_subplot(1, 1, 1)
            # Adjust the logo's position (move it up or down)
            logo_y_position = 0.80  # Adjust this value (0.7 is the default)
            ax_logo.set_position([0.25,logo_y_position, 0.2, 0.2])  # [left, bottom, width, height]
            # Adjust the logo's size
            logo_width = 0.2  # Adjust this value (0.2 is the default)
            ax_logo.imshow(logo_img, extent=[0, logo_width, 0, logo_width * logo_img.shape[0] / logo_img.shape[1]])
            # Turn off axis for the logo subplot
            ax_logo.axis('off')
            ax_logo.set_frame_on(False)
            text_x = 0.44
            text_y = 1.05 # Adjust the y-coordinate as needed
            ax.text(text_x, text_y, "Garments Pvt Limited", fontsize = 40, color='black')
            ax.text(0.3, 0.85, "(Knitting Division)", fontsize = 40,color='black')
            ax.text(0.18,0.62 ,f"Inspection Report for Date: {current_date}", fontsize = 40, color='black')
            ax.text(-0.1, 0.35, "Machine Dia: 30I ", fontsize = 40, color='black')
            ax.text(-0.1, 0.12, "Dc No:", fontsize = 40, color='black')
            ax.text(-0.1, -0.10, "Fabric:", fontsize = 40, color='black')
            ax.axis('off')
            defect_log_df = pd.DataFrame(data6, columns=['timestamp', 'defect_type'])
            defect_log_df['date'] = defect_log_df['timestamp'].dt.date
            defect_log_df['time'] = defect_log_df['timestamp'].dt.strftime('%H:%M:%S')  # Format the time as HH:MM:SS
            defect_log_df.drop(columns=['timestamp'], inplace=True)
            query = '''
        WITH LastEntry AS (
            SELECT MAX(timestamp) AS last_entry_timestamp
            FROM roll_details
            WHERE DATE(timestamp) = %s::date - interval '1 day'
        )
        
        SELECT
            roll_number,
            EXTRACT(HOUR FROM timestamp) || ':' || EXTRACT(MINUTE FROM timestamp) || ':' || EXTRACT(SECOND FROM timestamp) AS roll_start_time,
            roll_name,       -- Added the 'roll_name' column
            revolution       -- Added the 'revolution' column
        FROM roll_details
        WHERE DATE(timestamp) = %s::date OR timestamp = (SELECT last_entry_timestamp FROM LastEntry)
        ORDER BY timestamp ASC;
    '''

            cursor.execute(query, (current_date, current_date))
            data = cursor.fetchall()

            # Create a list with the desired columns
            roll_details_cellText = [
                [str(row[0]), row[1], str(row[2]), str(row[3])]
                for row in data
            ]

            # Create the DataFrame with the modified data
            roll_details_df = pd.DataFrame(roll_details_cellText, columns=['Roll id', 'Start Time', 'Knit id', 'No of Doff'])

            # Calculate Roll End Time based on the next row's Roll Start Time
            roll_details_df['End Time'] = roll_details_df['Start Time'].shift(-1)

            # Set the "Roll End Time" to the end of the day for the last row
            last_row_index = len(roll_details_df) - 1
            if last_row_index >= 0:
                roll_details_df.at[last_row_index, 'End Time'] = '23:59:59'  # Set to the end of the day

            # Drop the last row as it doesn't have a corresponding next row
            roll_details_df = roll_details_df.dropna(subset=['Start Time', 'End Time'])
            
            first_row_index = 0
            roll_details_df['Start Time'] = pd.to_datetime(roll_details_df['Start Time'], format="%H:%M:%S.%f", errors='coerce', exact=False, infer_datetime_format=True)
            roll_details_df['End Time'] = pd.to_datetime(roll_details_df['End Time'], format="%H:%M:%S.%f", errors='coerce', exact=False, infer_datetime_format=True) 
            roll_details_df['Start Time'] = roll_details_df['Start Time'].dt.strftime('%H:%M')
            roll_details_df['End Time'] = roll_details_df['End Time'].dt.strftime('%H:%M')

            # Calculate and assign 'Time Taken' for the first row
            start = pd.to_datetime(roll_details_df.at[first_row_index, 'Start Time'])
            end = pd.to_datetime(roll_details_df.at[first_row_index, 'End Time']) - timedelta(days=1)
            diff = end - start
            hours = int(diff.seconds // 3600)
            minutes = int((diff.seconds // 60) % 60)
            roll_details_df.at[first_row_index, 'Time Taken'] = f"{hours}h {minutes}m"

            # Calculate and assign 'Time Taken' for other rows
            for row_index in range(1, len(roll_details_df) - 1):
                time_taken_minutes = (pd.to_datetime(roll_details_df.at[row_index, 'End Time']) - pd.to_datetime(roll_details_df.at[row_index, 'Start Time'])).total_seconds() / 60
                hours = int(time_taken_minutes // 60)
                minutes = int(time_taken_minutes % 60)
                roll_details_df.at[row_index, 'Time Taken'] = f"{hours}h {minutes}m"

            defect_counts = []
            defect_types_to_separate = ['lycra', 'needln', 'hole']
            # Initialize empty lists for each defect type
            lycra_counts = []
            needle_counts = []
            hole_counts = []
            other_defects = []
            # Start with the beginning of the day for the first row
            start_time = '00:00'
            for index, row in roll_details_df.iterrows():
                roll_start_time = pd.Timestamp(row['Start Time'])
                # Determine the end_time for the current roll entry
                if index < len(roll_details_df) - 1:
                    Roll_End_Time = pd.Timestamp(roll_details_df.at[index + 1, 'Start Time'])
                else:
                    # For the last row, end with the end of the day
                    Roll_End_Time = roll_start_time.replace(hour=23, minute=59)
                end_time = Roll_End_Time.strftime('%H:%M')
                defect_counts = {}  # Initialize defect counts for each roll
                for defect_type in defect_types_to_separate:
                    defect_counts[defect_type] = 0  # Initialize counts for the specific defect types
                other_defect_counts = {}  # Initialize counts for other defect types
                for j in range(0, len(defect_log_df)):
                    log_time = pd.Timestamp(defect_log_df.at[j, 'time'])
                    time = log_time.strftime('%H:%M')
                    defect_type = defect_log_df.at[j, 'defect_type']
                    if defect_type in defect_types_to_separate:
                        if start_time <= time <= end_time:
                            defect_counts[defect_type] += 1
                    else:
                        # Count other defects
                        if start_time <= time <= end_time:
                            if defect_type not in other_defect_counts:
                                other_defect_counts[defect_type] = 1
                            else:
                                other_defect_counts[defect_type] += 1
                
                start_time = end_time
                lycra_counts.append(defect_counts['lycra'])
                needle_counts.append(defect_counts['needln'])
                hole_counts.append(defect_counts['hole'])
                if not other_defect_counts:
                    other_defects.append('0')
                else:
                    # Convert other_defect_counts dictionary to a formatted string
                    formatted_other_defects = ', '.join([f'{defect_type}: {count}' for defect_type, count in other_defect_counts.items()])
                    other_defects.append(formatted_other_defects)

            roll_details_df['Lycra Defects'] = lycra_counts
            roll_details_df['Needle Defects'] = needle_counts
            roll_details_df['Hole Defects'] = hole_counts
            roll_details_df['Other Defects'] = other_defects
            roll_details_df['Defect Counts'] = defect_counts
            roll_details_df.fillna("running", inplace=True)
            roll_details_df.drop(columns=['Defect Counts'], inplace=True)            
            roll_details_df['Roll Weight'] = ''
            roll_details_df['Decision'] = ''
            roll_details_df['Sign'] = ''
            column_names_to_select = ['Knit id', 'Start Time', 'End Time', 'Time Taken', 'Roll id', 'No of Doff', 'Lycra Defects', 'Needle Defects', 'Hole Defects', 'Other Defects', 'Roll Weight', 'Decision', 'Sign']
            roll_details_df = roll_details_df[column_names_to_select]
            table_data = roll_details_df.values.tolist()
            # Convert the DataFrame to a list
            table = ax.table(cellText=table_data, colLabels=['Knit ID', 'Start\n Time', 'End\n Time', 'Time\n Taken', 'Roll\n Id', 'No\nof\nRevolutions', 'Lycra', 'Needline', 'Hole', 'Other','Roll\nWeight','Decision','Sign'], bbox=[-0.130, -1.75, 1.2, 1.5])
            # Set font size for column headers
            font_size = 18  # Adjust the font size as needed
            table.auto_set_font_size(False)
            table.set_fontsize(font_size)
            header_height = 0.13  # Adjust the header cell height as needed
            for key, cell in table.get_celld().items():
                if key[0] == 0:  # Header row
                    cell.set_height(header_height)
            table.auto_set_column_width([0,1,2,3,4,5,6,7,8,9])
            ax1.text(0.25, -0.3, "Remarks:", fontsize = 30, color='black')
            ax1.text(-0.10, -0.6, "Knitting Signature", fontsize = 30, color='black')
            ax1.text(0.80, -0.6, "Quality Incharge", fontsize = 30, color='black')
            ax2.axis('off')
            ax1.axis('off')
            pdf_pages.savefig(fig)
            plt.close(fig)
            pdf_pages.close() 
            pdf_buffer.seek(0)
            return pdf_buffer, True


def generate_pdf_performance(report_date):
    filename = f"SCM_MACHINE1_PERFORMANCE_REPORT_{report_date}.pdf"
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
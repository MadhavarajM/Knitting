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
import os, json
from configparser import ConfigParser


locale.setlocale(locale.LC_TIME, 'C')
encoding = 'utf-8'

def generate_plots_pdf(start_date, end_date, version, machine,countai_img, mill_img):
    # Connect to the database
    conn = psycopg2.connect(
            host='localhost',
            database='knitting',
            user='postgres',
            password='55555'
        )
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
        
        current_date = start_date + datetime.timedelta(days=i)
        new_date = current_date + datetime.timedelta(days=i+1)
        fig, (ax, ax1 , ax2) = plt.subplots(3, 1, figsize=(21, 29.7))
        plt.subplots_adjust(hspace=0.8)
        logo_path = countai_img
        logo_img = mpimg.imread(logo_path)
        ax_logo = fig.add_subplot(1, 1, 1)
        logo_y_position = 0.87  
        ax_logo.set_position([0.77, logo_y_position, 0.2, 0.2]) 
        logo_width = 0.2
        ax_logo.imshow(logo_img, extent=[0, logo_width, 0, logo_width * logo_img.shape[0] / logo_img.shape[1]])
        ax_logo.axis('off')
        ax_logo.set_frame_on(False)
        logo_path_2 =  mill_img
        logo_img = mpimg.imread(logo_path_2)
        ax_logo = fig.add_subplot(1, 1, 1)
        logo_y_position = 0.91
        ax_logo.set_position([0.03,logo_y_position, 0.10, 0.10])  
        logo_width = 0.2
        ax_logo.imshow(logo_img, extent=[0, logo_width, 0, logo_width * logo_img.shape[0] / logo_img.shape[1]])
        ax_logo.axis('off')
        ax_logo.set_frame_on(False)
        ax.text(0.08,1.50 ,f"Inspection Report for Date: {current_date}  ", fontsize = 40, color='black')
        ax.text(-0.1, 1.00, f"Machine Name: ", fontsize = 40, color='black')
        ax.text(-0.1, 0.75, "Machine Dia:", fontsize = 40, color='black')
        ax.text(-0.1, 0.50, "Fabric:", fontsize = 40, color='black')
        ax.axis('off')
        ax1.axis('off')
        ax2.axis('off')
            
        query = '''SELECT
	    rd.roll_number,
	    rd.roll_start_date,
	    rd.roll_name,
	    rd.roll_id,
	    rd.revolution,
	    rd.timestamp
	    FROM
	    roll_details AS rd
	    WHERE
	    rd.timestamp >= %s::timestamp + '06:00:00'::interval 
	    AND rd.timestamp < %s::timestamp + '06:00:00'::interval
	    ORDER BY rd.timestamp;'''


        cursor.execute(query, (current_date, new_date))
        data = cursor.fetchall()


        roll_details_cellText = [
        [str(row[0]), row[1], str(row[2]), int(row[3]), (row[4])]
        for row in data]

        # Create the DataFrame with the modified data
        roll_details_df = pd.DataFrame(roll_details_cellText, columns=['Roll id', 'Start Time', 'Knit id', 'id','No of Doff'])

        # Calculate Roll End Time based on the next row's Roll Start Time
        roll_details_df['End Time'] = roll_details_df['Start Time'].shift(-1)

        if roll_details_df.empty:
            pdf_pages.close()
            return pdf_buffer, False

        if len(roll_details_df) == 1:
            roll_details_df.fillna("running", inplace=True)
            roll_details_df['Time Taken'] = "running"
            roll_details_df['Start Time'] = roll_details_df['Start Time'].dt.strftime('%H:%M')

        else:

            last_row_index = len(roll_details_df) - 1
            
            if last_row_index >= 0:
                roll_details_df.at[last_row_index, 'End Time'] = 'running'  

            roll_details_df = roll_details_df.dropna(subset=['Start Time', 'End Time'])

            first_row_index = 0
            roll_details_df['Start Time'] = pd.to_datetime(roll_details_df['Start Time'], format="%H:%M:%S.%f", errors='coerce', exact=False)
            roll_details_df['End Time'] = pd.to_datetime(roll_details_df['End Time'], format="%H:%M:%S.%f", errors='coerce', exact=False) 
            roll_details_df['Start Time'] = roll_details_df['Start Time'].dt.strftime('%H:%M')
            roll_details_df['End Time'] = roll_details_df['End Time'].dt.strftime('%H:%M')

            start = pd.to_datetime(roll_details_df.at[first_row_index, 'Start Time'])
            end = pd.to_datetime(roll_details_df.at[first_row_index, 'End Time']) - timedelta(days=1)
            diff = end - start
            hours = int(diff.seconds // 3600)
            minutes = int((diff.seconds // 60) % 60)
            roll_details_df.at[first_row_index, 'Time Taken'] = f"{hours}h {minutes}m"

            for row_index in range(1, len(roll_details_df) - 1):
                start_time = pd.to_datetime(roll_details_df.at[row_index, 'Start Time'])
                end_time = pd.to_datetime(roll_details_df.at[row_index, 'End Time'])
                
                if end_time < start_time:
                    end_time += pd.DateOffset(days=1)
                
                time_difference = end_time - start_time
                total_seconds = time_difference.total_seconds()
                
                hours = int(total_seconds // 3600)
                minutes = int((total_seconds % 3600) // 60)
                roll_details_df.at[row_index, 'Time Taken'] = f"{hours}h {minutes}m"


        id_list = roll_details_df['id'].tolist()
        fetched_data = []
        for id_value in id_list:
            query = """
            SELECT
            dd.timestamp AS timestamp,
            dt.defect_name AS defect_type,
            dd.revolution AS revolution,
            rd.roll_name AS roll_name,
            dd.roll_id AS defect_roll_id
            FROM defect_details dd
            JOIN alarm_status AS a ON a.defect_id = dd.defect_id
            JOIN defect_type AS dt ON dd.defecttyp_id = dt.defecttyp_id
            JOIN roll_details AS rd ON dd.roll_id = rd.roll_id
            WHERE dd.roll_id = %s
            ORDER BY dd.timestamp;
            """
            
            cursor.execute(query, (id_value,))
            data = cursor.fetchall()
            
            fetched_data.append(data)


        columns = ["timestamp", "defect_type", "revolution", "roll_name", "defect_roll_id"]
        defect_df = pd.DataFrame([item for sublist in fetched_data for item in sublist], columns=columns)
        
        lycra_counts = []
        needle_counts = []
        hole_counts = []
        other_defects = []

        for roll_id in roll_details_df['id']:
            
            roll_defects = defect_df[defect_df['defect_roll_id'] == roll_id]
            defect_counts = {'lycra': 0, 'needln': 0, 'hole': 0}
            other_defect_counts = {}

            for _, defect_row in roll_defects.iterrows():
                defect_type = defect_row['defect_type']

                if defect_type in defect_counts:
                    defect_counts[defect_type] += 1
                else:
                    if defect_type not in other_defect_counts:
                        other_defect_counts[defect_type] = 1
                    else:
                        other_defect_counts[defect_type] += 1

            lycra_counts.append(defect_counts['lycra'])
            needle_counts.append(defect_counts['needln'])
            hole_counts.append(defect_counts['hole'])

            if not other_defect_counts:
                other_defects.append('0')
            else:
                formatted_other_defects = ', '.join([f'{defect_type}: {count}' for defect_type, count in other_defect_counts.items()])
                other_defects.append(formatted_other_defects)

        
        roll_details_df['Lycra Defects'] = lycra_counts
        roll_details_df['Needle Defects'] = needle_counts
        roll_details_df['Hole Defects'] = hole_counts
        roll_details_df['Other Defects'] = other_defects
        roll_details_df.fillna("running", inplace=True)
        roll_details_df['No of Doff'] = pd.to_numeric(roll_details_df['No of Doff'], errors='coerce')
        roll_details_df = roll_details_df[(roll_details_df['No of Doff'].notna()) & (roll_details_df['No of Doff'] != 0)]
        roll_details_df['Knit id'] = range(1, len(roll_details_df) + 1)
        defect_df = defect_df.merge(roll_details_df[['id', 'Knit id']], left_on='defect_roll_id', right_on='id', how='left')
        defect_df.drop(columns=['defect_roll_id','id','roll_name'], inplace=True)
        roll_details_df.drop(columns=['id'], inplace=True)
        roll_details_df.drop(columns=['Roll id'], inplace=True)
        roll_details_df['Insception'] = ''

        column_names_to_select = ['Knit id', 'Start Time', 'End Time', 'Time Taken', 'No of Doff', 'Lycra Defects', 'Needle Defects', 'Hole Defects', 'Other Defects','Insception']
        roll_details_df = roll_details_df[column_names_to_select]
        table_data = roll_details_df.values.tolist()

        table = ax.table(cellText=table_data, colLabels=['Knit ID', 'Start\n Time', 'End\n Time', 'Time\n Taken',  'No\nof\nDoff', 'Lycra', 'Need\nline', 'Hole', 'Other','Inspection'], bbox=[-0.130, -2.8, 1.2, 3.0])
        font_size = 18 
        table.auto_set_font_size(False)
        table.set_fontsize(font_size)
        header_height = 0.13 
        for key, cell in table.get_celld().items():
            if key[0] == 0: 
                cell.set_height(header_height)
        table.auto_set_column_width([0,1,2,3,4,5,6,7,8,9])
        ax1.text(-0.13, -1.2, "Remarks:", fontsize = 30, color='black')
        ax1.text(-0.13, -1.58, "Knitting Incharge", fontsize = 30, color='black')
        ax1.text(0.85, -1.58, "Quality Incharge", fontsize = 30, color='black')
        current_datetime = datetime.datetime.now()
        formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M")
        ax1.text(0.71, -2.1, f"Pdf generated on : {formatted_datetime}", fontsize = 24, color='black')
        ax1.text(0.75, -2.3, f"Version : {version}", fontsize = 24, color='black')
        pdf_pages.savefig(fig)
        plt.close(fig)

        rows_per_page = 40
        num_pages = -(-len(defect_df) // rows_per_page)
        for page_num in range(num_pages):
            start_idx = page_num * rows_per_page
            end_idx = (page_num + 1) * rows_per_page
            defect_log_table_data_page = defect_df[start_idx:end_idx].copy()  
            defect_log_table_data_page['timestamp'] = pd.to_datetime(defect_log_table_data_page['timestamp'])
            defect_log_table_data_page['time_only'] = defect_log_table_data_page['timestamp'].dt.strftime('%H:%M:%S')
            defect_log_table_data_page.drop(columns=['timestamp'], inplace=True)
            column_names_to_select = ['time_only', 'defect_type', 'revolution', 'Knit id']
            defect_log_table_data_page = defect_log_table_data_page[column_names_to_select]
            defect_log_table_data_page['Shift'] = "Unknown"  
            shift_a_start = '06:00:00'
            shift_b_start = '14:30:00'
            shift_c_start = '23:00:00'
            defect_log_table_data_page.loc[defect_log_table_data_page['time_only'].between(shift_a_start, shift_b_start), 'Shift'] = "Shift A"
            defect_log_table_data_page.loc[defect_log_table_data_page['time_only'].between(shift_b_start, shift_c_start), 'Shift'] = "Shift B"
            defect_log_table_data_page.loc[~defect_log_table_data_page['time_only'].between(shift_a_start, shift_b_start) & ~defect_log_table_data_page['time_only'].between(shift_b_start, shift_c_start), 'Shift'] = "Shift C"
            defect_log_table_data_page_modified = defect_log_table_data_page.values.tolist()
            fig, ax4 = plt.subplots(figsize=(21, 29.7))
            logo_path = countai_img
            logo_img = mpimg.imread(logo_path)
            ax_logo = fig.add_subplot(1, 1, 1)
            ax_logo.imshow(logo_img)
            ax_logo.axis('off')
            logo_y_position = 0.87  
            ax_logo.set_position([0.77, logo_y_position, 0.2, 0.2])  
            logo_width = 0.2 
            ax_logo.imshow(logo_img, extent=[0, logo_width, 0, logo_width * logo_img.shape[0] / logo_img.shape[1]])
            ax_logo.axis('off')
            ax_logo.set_frame_on(False)
            ax4.set_title(f"Defect Log Report", fontsize=24)
            ax4.axis('off')
            title_height = 0.1  
            table_height = 1.0  
            table_bottom = 1 - title_height - table_height 
            table = ax4.table(
            cellText=defect_log_table_data_page_modified,
            colLabels=['Time', 'Defect Type','Revolution', 'Rollno' , 'Shift'],
            cellLoc='center',
            loc='center',
            bbox=[0.1, table_bottom, 0.8, table_height])
            table.auto_set_font_size(False)
            table.set_fontsize(20)
            table.auto_set_column_width([5, 5, 5])
            table.scale(1, 2)
            pdf_pages.savefig(fig)
            plt.close(fig)
    pdf_pages.close()
    cursor.close()
    conn.close()
    pdf_buffer.seek(0)
    return pdf_buffer, True




def generate_pdf_performance(report_date):
    config = ConfigParser()
    config.read('config_webui.ini')
    directory_path = config.get('report', 'outputPDF_directory_path')
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
    millname = config.get('report', 'millname')
    version = config.get('report', 'version')
    machine =  config.get('report', 'machine')
    countai_img = config.get('report', 'countai_img')
    mill_img = config.get('report', 'mill_img')  
    filename = f"{directory_path}/{millname}_{report_date}.pdf"
    pdf_buffer, has_data = generate_plots_pdf(report_date, report_date,version, machine,countai_img, mill_img)
    local_path = './static/report/current_report.pdf'
    if has_data:
        with open(filename, 'wb') as f:
            f.write(pdf_buffer.getvalue())
        with open(local_path, 'wb') as f:
            f.write(pdf_buffer.getvalue())
        print(f"PDF generated for {report_date}")
        return True
    else:
        print(f"No data found for {report_date}. PDF not generated.")
        return False


# generate_pdf_performance('2023-10-26')  

   

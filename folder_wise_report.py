import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from collections import defaultdict
import re
from matplotlib.backends.backend_pdf import PdfPages

def process_defect_subfolder(defect_subfolder_path, defect_name, data):
    for filename in os.listdir(defect_subfolder_path):
        if filename.endswith(".jpg"):
            match = re.search(pattern, filename)
            if match:
                image_name = filename
                data.loc[len(data)] = [image_name, defect_name]

def collect_data(main_folder_path, pattern):
    data = pd.DataFrame(columns=['Image', 'Defect'])

    for roll_no in os.listdir(main_folder_path):
        roll_path = os.path.join(main_folder_path, roll_no)
        if os.path.isdir(roll_path):
            for date_folder in os.listdir(roll_path):
                date_path = os.path.join(roll_path, date_folder)
                if os.path.isdir(date_path):
                    for tp_or_fp in os.listdir(date_path):
                        tp_or_fp_path = os.path.join(date_path, tp_or_fp)
                        if os.path.isdir(tp_or_fp_path) and (tp_or_fp == 'TP'):
                            for defect_folder in os.listdir(tp_or_fp_path):
                                defect_folder_path = os.path.join(tp_or_fp_path, defect_folder)
                                if os.path.isdir(defect_folder_path):
                                    process_defect_subfolder(defect_folder_path, defect_folder, data)

    return data



    

def plot_image_distribution(data, pdf, title):
    hourly_counts_per_defect = defaultdict(lambda: defaultdict(int))

    for defect_type in data['Defect'].unique():
        defect_data = data[data['Defect'] == defect_type]
        for image_name in defect_data['Image']:
            timestamp_str = re.search(pattern, image_name).group()
            datetime_str = re.sub(r'\+\d{2}_\d{2}_\d{2}', '', timestamp_str)
            datetime_obj = datetime.strptime(datetime_str, "%Y-%m-%d_%H_%M_%S.%f")
            hourly_counts_per_defect[defect_type][datetime_obj.hour] += 1

    defect_types = list(hourly_counts_per_defect.keys())
    hours = list(range(24))
    bar_width = 0.2
    offsets = [i * bar_width for i in range(len(defect_types))]

    plt.figure(figsize=(20, 6))

    for i, defect_type in enumerate(defect_types):
        hourly_counts = [hourly_counts_per_defect[defect_type][hour] for hour in hours]
        bars = plt.bar([hour + offsets[i] for hour in hours], hourly_counts, width=bar_width, label=defect_type)

        for bar in bars:
            height = bar.get_height()
            #if height != 0:
            plt.annotate(f'{height}', xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3),  # 3 points vertical offset
                            textcoords="offset points",
                            ha='center', va='bottom')

    plt.xlabel('Time of the Day(Hour)')
    plt.ylabel('Number of Defects')
    plt.title(title)  # Add title
    plt.xticks([hour + (len(defect_types) - 1) * bar_width / 2 for hour in hours], hours)
    plt.legend()
    pdf.savefig()  # Save the plot to the PDF
    plt.close()  # Close the figure

# Get the date input from the user
date = input("Enter the date (e.g.,07-08-2023):")

# Define the main folder path up to "kpr"
main_folder_path = f"C:/Users/MadhavaRaj/Downloads/{date}"
pattern = r"\d{4}-\d{2}-\d{2}_\d{2}_\d{2}_\d{2}\.\d{6}\+\d{2}_\d{2}_\d{2}"

# Collect data and create a PDF file for plots
data_tp = collect_data(main_folder_path, pattern)


# Create a single PDF to save both TP and FP plots
pdf_filename = f'True_Positive_KPR_{date}.pdf'
with PdfPages(pdf_filename) as pdf:
    plot_image_distribution(data_tp, pdf, f'Defect Distribution by Hour (TP) - {date}')
    

print(f'Plots saved to {pdf_filename}')

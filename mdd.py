import psycopg2
import matplotlib.pyplot as plt
from collections import defaultdict
from matplotlib.backends.backend_pdf import PdfPages
from io import BytesIO

def calculate_iou(box1,box2):
    if box1 is None or box2 is None:
        return 0.0
    x1, y1 = box1[0]
    x2, y2 = box1[1]
    x3, y3 = box2[0]
    x4, y4 = box2[1]
    x_inter1 = max(x1, x3)
    y_inter1 = max(y1, y3)
    x_inter2 = min(x2, x4)
    y_inter2 = min(y2, y4)


    inter_area = max(0, x_inter2 - x_inter1 + 1) * max(0, y_inter2 - y_inter1 + 1)

    box1_area = (x2 - x1 + 1) * (y2 - y1 + 1)
    box2_area = (x4 - x3 + 1) * (y4 - y3 + 1)

    iou = inter_area / float(box1_area + box2_area - inter_area)
    return iou

def calculation(box1, box2):
    if box1 is None or box2 is None:
        return 0, 0

    x1, y1 = box1[0]
    x2, y2 = box1[1]
    x3, y3 = box2[0]
    x4, y4 = box2[1]

    x_inter1 = max(x1, x3)
    y_inter1 = max(y1, y3)
    x_inter2 = min(x2, x4)
    y_inter2 = min(y2, y4)

    inter_area = max(0, x_inter2 - x_inter1 + 1) * max(0, y_inter2 - y_inter1 + 1)

    box1_area = (x2 - x1 + 1) * (y2 - y1 + 1)
    box2_area = (x4 - x3 + 1) * (y4 - y3 + 1)
    union_area = box1_area + box2_area - inter_area

    mdd_area = box1_area - inter_area
    gt_area = box2_area - inter_area
    
    
    return mdd_area, gt_area

def formula(iou, area_1, area_2):
    if iou + area_2 == 0:
        return 0.0 
    F = (iou - area_1)/(iou + area_2)
    return F

def classify_label(original_label, original_coords, copied_coords,copied_label):
    if original_label is not None and copied_label is None and original_coords is not None and copied_coords is None:
        return "fp"
    else:
        iou = calculate_iou(original_coords,copied_coords)
        area_1, area_2 = calculation(original_coords, copied_coords)
        check = formula(iou, area_1, area_2)
        if iou == 1.0:
            if original_label == copied_label:
                return "tp"
            else:
                return "fp"
        elif iou == 0.0:
            return "gt"
        else :
            if check < 0.4:
                return 'tp'
            else :
                return 'fp'

def generate_stacked_bar_graph_with_percentages(pdf_pages , selected_date, millname):
    # Connect to the PostgreSQL Database
    
    conn = psycopg2.connect(
        database="plot",
        user="postgres",
        password="manager",
        host="localhost",
        port="5432"
    )
    cursor = conn.cursor()
    cursor.execute('''SELECT DISTINCT rollid FROM checking WHERE timestamp::text LIKE %s AND mill = %s''',(f"{selected_date}%",millname))
    unique_rollids = []
    for row in cursor.fetchall():
        unique_rollids.append(row[0])
    print("Unique rollid values:", unique_rollids)
    # Fetch data from the database for the selected date
    cursor.execute("SELECT original, modified, folder FROM checking WHERE timestamp::text LIKE %s AND mill = %s", (f"{selected_date}%",millname))
    data = cursor.fetchall()
    # Count TP and FP instances
    label_counts = defaultdict(lambda: {"tp": 0, "fp": 0, "gt" : 0})
    for entry in data:
        
        original_tuple, copied_tuple, folder = entry
        original_list = []
        copied_list = []
        if isinstance(original_tuple, dict):
            original_list = [original_tuple] 
        if isinstance(copied_tuple, dict):
            copied_list = [copied_tuple]  
        if isinstance(original_tuple, list):
            original_list = original_tuple  
        if isinstance(copied_tuple, list):
            copied_list = copied_tuple  
        for original_entry, copied_entry in zip(original_list, copied_list):
            original_label = original_entry.get("label")
            copied_label = copied_entry.get("label")
            original_coords = original_entry.get("original_coordinates")
            copied_coords = copied_entry.get("copied_coordinates")
            original_class = classify_label(original_label, original_coords, copied_coords,copied_label)
            if original_class == "tp":
                if original_label is not None:
                    label_counts[original_label]["tp"] += 1
            elif original_class == "fp":
                if original_label is not None:
                    label_counts[original_label]["fp"] += 1
            elif original_class == "gt":
                if original_label is not None:
                    label_counts[original_label]["gt"] += 1
    print(label_counts)
               
    fig, ax = plt.subplots(figsize=(25, 15))
    ax.set_title(f"TP,FP and GT Counts by Defects - {selected_date}", fontsize = 18)
    # Create Stacked Bar Graph
    labels = list(label_counts.keys())
    tp_counts = [label_counts[label]["tp"] for label in labels]
    fp_counts = [label_counts[label]["fp"] for label in labels]
    gt_counts = [label_counts[label]["gt"] for label in labels]
    
    ax.bar(labels, tp_counts, label="True Positives")
    ax.bar(labels, fp_counts, bottom=tp_counts, label="False Positives")
    ax.bar(labels, gt_counts, bottom=[tp + fp for tp, fp in zip(tp_counts, fp_counts)], label="Ground Truth")

    # Annotate the bars with TP, FP, and GT counts
    for i, (tp_count, fp_count,gt_count) in enumerate(zip(tp_counts, fp_counts,gt_counts)):
        total_count = tp_count + fp_count + gt_count
        center_y = total_count / 2
        if tp_count > 0:
            ax.annotate(f"TP: {tp_count}", (i, tp_count / 2), ha="center", va="center", color="white", fontsize=10, fontweight="bold")
        if fp_count > 0:
            ax.annotate(f"FP: {fp_count}", (i, tp_count + fp_count / 2), ha="center", va="center", color="black", fontsize=10, fontweight="bold")
        if gt_count > 0:
            ax.annotate(f"GT: {gt_count}", (i, tp_count + fp_count + gt_count / 2), ha="center", va="center", color="black", fontsize=10, fontweight="bold")

    annotation_info = []
    for label in labels:
        total_instances = label_counts[label]["tp"] + label_counts[label]["fp"] + label_counts[label]["gt"]
        tp_percentage = (label_counts[label]["tp"] / total_instances) * 100
        fp_percentage = (label_counts[label]["fp"] / total_instances) * 100
        gt_percentage = (label_counts[label]["gt"] / total_instances) * 100
        
        annotation_text = f"Defect type :{label} - TP Percentage: {tp_percentage:.2f}% and FP Percentage: {fp_percentage:.2f}%  and GT Percentage: {gt_percentage:.2f}% "
        annotation_info.append(annotation_text)
        annotation_text = '\n'.join(annotation_info)
    ax.text(0.5, -0.125, annotation_text, transform=ax.transAxes, fontsize=13, color='black', ha='center')
    pdf_pages.savefig(fig)
    plt.close(fig)

    for rollid in unique_rollids:
        cursor.execute("""
        SELECT original, modified, folder 
        FROM checking 
        WHERE timestamp::text LIKE %s
        AND rollid = %s AND mill = %s
    """,(f"{selected_date}%", rollid, millname))
        data = cursor.fetchall()
        # Count TP and FP instances
        label_counts = defaultdict(lambda: {"tp": 0, "fp": 0, "gt" : 0})
        for entry in data:
            
            original_tuple, copied_tuple, folder = entry
            original_list = []
            copied_list = []
            if isinstance(original_tuple, dict):
                original_list = [original_tuple] 
            if isinstance(copied_tuple, dict):
                copied_list = [copied_tuple]  
            if isinstance(original_tuple, list):
                original_list = original_tuple  
            if isinstance(copied_tuple, list):
                copied_list = copied_tuple  
            for original_entry, copied_entry in zip(original_list, copied_list):
                original_label = original_entry.get("label")
                copied_label = copied_entry.get("label")
                original_coords = original_entry.get("original_coordinates")
                copied_coords = copied_entry.get("copied_coordinates")
                original_class = classify_label(original_label, original_coords, copied_coords,copied_label)
                if original_class == "tp":
                    if original_label is not None:
                        label_counts[original_label]["tp"] += 1
                elif original_class == "fp":
                    if original_label is not None:
                        label_counts[original_label]["fp"] += 1
                elif original_class == "gt":
                    if original_label is not None:
                        label_counts[original_label]["gt"] += 1
        print(label_counts)
                
        fig, ax = plt.subplots(figsize=(25, 15))
        ax.set_title(f"TP,FP and GT Counts by Defects for Rollid {rollid} on {selected_date}",fontsize = 18)
        # Create Stacked Bar Graph
        labels = list(label_counts.keys())
        tp_counts = [label_counts[label]["tp"] for label in labels]
        fp_counts = [label_counts[label]["fp"] for label in labels]
        gt_counts = [label_counts[label]["gt"] for label in labels]
        
        ax.bar(labels, tp_counts, label="True Positives")
        ax.bar(labels, fp_counts, bottom=tp_counts, label="False Positives")
        ax.bar(labels, gt_counts, bottom=[tp + fp for tp, fp in zip(tp_counts, fp_counts)], label="Ground Truth")

        # Annotate the bars with TP, FP, and GT counts
        for i, (tp_count, fp_count,gt_count) in enumerate(zip(tp_counts, fp_counts,gt_counts)):
            total_count = tp_count + fp_count + gt_count
            center_y = total_count / 2
            if tp_count > 0:
                ax.annotate(f"TP: {tp_count}", (i, tp_count / 2), ha="center", va="center", color="white", fontsize=10, fontweight="bold")
            if fp_count > 0:
                ax.annotate(f"FP: {fp_count}", (i, tp_count + fp_count / 2), ha="center", va="center", color="black", fontsize=10, fontweight="bold")
            if gt_count > 0:
                ax.annotate(f"GT: {gt_count}", (i, tp_count + fp_count + gt_count / 2), ha="center", va="center", color="black", fontsize=10, fontweight="bold")

        annotation_info = []
        for label in labels:
            total_instances = label_counts[label]["tp"] + label_counts[label]["fp"] + label_counts[label]["gt"]
            tp_percentage = (label_counts[label]["tp"] / total_instances) * 100
            fp_percentage = (label_counts[label]["fp"] / total_instances) * 100
            gt_percentage = (label_counts[label]["gt"] / total_instances) * 100
            
            annotation_text = f"Defect type :{label} - TP Percentage: {tp_percentage:.2f}% and FP Percentage: {fp_percentage:.2f}%  and GT Percentage: {gt_percentage:.2f}% "
            annotation_info.append(annotation_text)
            annotation_text = '\n'.join(annotation_info)
        ax.text(0.5, -0.125, annotation_text, transform=ax.transAxes, fontsize=13, color='black', ha='center')
        pdf_pages.savefig(fig)
        plt.close(fig)

    return annotation_info, pdf_pages

if __name__ == '__main__':
    selected_date = input("Enter the date (YYYY-MM-DD): ")
    millname = input("Enter the millname (KPR1/SCM1): ")
    filename = f"MODEL_DETECTED_GRAPH_{selected_date}.pdf"
    pdf_buffer = BytesIO()
    pdf_pages = PdfPages(pdf_buffer)
    annotation_info, pdf_pages = generate_stacked_bar_graph_with_percentages(pdf_pages, selected_date, millname)
    pdf_pages.close()

    with open(filename, 'wb') as f:
        f.write(pdf_buffer.getvalue())

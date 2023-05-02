from datetime import datetime
import os
import platform
import subprocess

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape, letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (Image, PageBreak, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)
from reportlab.lib.units import inch
import pandas as pd

def create_pdf_report(data, filename):
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(filename, pagesize=A4, leftMargin=inch, rightMargin=inch)

    if data["gender"] == 'f':
        gender = "female"
    else:
        gender = "male"

    # Basic data
    basic_data = [
        ["Name", data["name"], ""],
        ["Age", data["age"], ""],
        ["Gender", gender, ""],
        ["Address", data["address"], ""],
        ["Doctor", data["doctor"], ""],
        ["User remark", data["remark"], ""],
    ]

    # Add user photo
    if os.path.exists(data["photo_location"]):
        user_photo = Image(data["photo_location"])
        user_photo.drawHeight = 70
        user_photo.drawWidth = 70
    else:
        user_photo = "Image not found"

    # Add offline.png image
    if os.path.exists(data["offline_image"]):
        last_run_image = Image(data["offline_image"])
        last_run_image.drawHeight = 200
        last_run_image.drawWidth = 200
    else:
        last_run_image = "Image not found"

    hardware_data = [
        ["Acquisition System", data["acquisitionSys"],""],
        ["Sampling Rate (Hz)", data["sampleRate"],""],
        ["Number of Channels", data["chnNUM"],""],
        ["Monitor Selected", data["monitor"],""],
    ]

    processing_data = [
        ["Run Mode", data["run_mode"],""],
        ["Synchronous Mode", data["sync_mode"],""],
        ["Feature Extraction", data["feature_extraction"],""],
        ["Number of Blocks", data["num_of_blocks"],""],
        ["Data Saved Path", data["data_saved_path "],""],
    ]

    last_run_data = [
        ["Accuracy (%)", data["accuracy"],""],
        ["ITR (bits/min)", data["ITR"],""],
        ["Accuracy (%) and\nITR (bits/min)\nover window length", "",""],
        ["Commenced Date\nand Time", data["timeAndDate"],""],
        ["Total Run Time", data["total_time"],""],
        ["Keyboard Name", data["keyboard_name"],""],
    ]
    
    
    # Combine data and create tables
    all_data = basic_data + hardware_data + processing_data + last_run_data
    table = Table(all_data, colWidths=[1.5 * inch, 3 * inch, 1.5 * inch])

    table.setStyle(TableStyle([
        ('SPAN', (2, 0), (2, 5)),  # Span for user photo
        *([('SPAN', (1, i), (2, i)) for i in range(6, 21)]),  # Span across for indices 6 to 17
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('WORDWRAP', (0, 0), (-1, -1), 'CJK'),
        ('ALIGN', (2, 0), (2, 5), 'CENTER'),  # Center user_photo horizontally
        ('VALIGN', (2, 0), (2, 5), 'MIDDLE'),  # Center user_photo vertically
        ('ALIGN', (1, 17), (2, 17), 'CENTER'),  # Center last_run_image horizontally
        ('VALIGN', (1, 17), (2, 17), 'MIDDLE'),  # Center last_run_image vertically
    ]))

    # Insert images
    table._cellvalues[0][2] = user_photo
    table._cellvalues[17][1] = last_run_image

    # Add table to the report
    story = [table]

    # Add keyboard_processing_table
    story.append(PageBreak())  # Add a page break
    story.append(Paragraph("Keyboard Processing Table:", styles['Heading2']))


    # Add column headers to the keyboard_processing_table_data
    
    column_headers = ["Key\nName", "Frequency\n(Hz)", "Phase\n(rad)", "Training\nAccuracy (%)", "Testing\nAccuracy (%)", "No of\nOutputs"]  # Replace these with the actual column headers
    keyboard_processing_table_data = [column_headers] + data["keyboard_processing_table"]
    keyboard_processing_table = Table(keyboard_processing_table_data)

    # Apply styles to the keyboard_processing_table
    keyboard_processing_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    
    story.append(keyboard_processing_table)

    doc.build(story)


# You need to implement this function to convert the QTableWidget data to a list of lists format.
def convert_qtablewidget_to_list(qtable_widget):
    
    data = []
    for row in range(qtable_widget.rowCount()):
        row_data = []
        for col in range(qtable_widget.columnCount()):
            item = qtable_widget.item(row, col)
            row_data.append(item.text() if item else "")
        data.append(row_data)
        
    return data


# the main function to call the report
def create_pdf_main(win):
    
    
    itr_value = "N/A"
    accuracy = "N/A"
    if win.config.MODE == "TRAIN":
        filepath = os.path.join(win.config.resultPath, win.config.personName, 'record', f'{win.config.prefix_with_time}offline.csv')
        if os.path.exists(filepath):
            df = pd.read_csv(filepath)
            filtered_data = df[df['Window Length'] == win.config.winLEN]
            accuracy = round(filtered_data['Accuracy'].mean()*100,2)
            itr_value = round(filtered_data['ITR'].mean(),2)
        else:
            itr_value = "N/A"
            accuracy = "N/A"
    elif win.config.MODE == "TEST" or win.config.MODE == "DEBUG":
        
        filepath = os.path.join(win.config.resultPath, win.config.personName, 'record', f'{win.config.prefix_with_time}trackEpoch.csv')
        # filepath = os.path.join(win.config.resultPath, win.config.personName, 'record', f'{win.config.prefix}online.csv')
        if os.path.exists(filepath):
            df = pd.read_csv(filepath)
            # Calculate the number of correct matches
            correct_matches = (df['event'] == df['result']).sum()
            # Calculate the total number of matches
            total_matches = len(df)
            # Calculate accuracy
            accuracy = correct_matches / total_matches

            from OperationSystem.AnalysisProcess.OperatorMethod.utils import ITR

            itr_value = ITR(win.config.targetNUM, accuracy, win.config.winLEN)
            accuracy = round(accuracy * 100, 2)
        else:
            itr_value = "N/A"
            accuracy = "N/A"

            
    elif win.config.MODE == "USE":
        itr_value = "N/A"
        accuracy = "N/A"
    
    
    date_str = win.config.prefix_with_time.split('_')[-3]
    time_str = win.config.prefix_with_time.split('_')[-2]
    date_time_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]} {time_str[:2]}:{time_str[2:4]}:{time_str[4:]}"

    date_time_obj = datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S')
    
    # Format date and time for the report
    formatted_date_time = date_time_obj.strftime("%B %d, %Y, %I:%M %p")

    
    # Build the data dictionary
    data = {
        "name": win.user_manager.current_user.name,
        "age": win.user_manager.current_user.age,
        "gender": win.user_manager.current_user.gender,
        "address": win.user_manager.current_user.address,
        "doctor": win.user_manager.current_user.doctor,
        "remark": win.user_manager.current_user.remark,
        "photo_location": win.user_manager.current_user.photo_location,
        "acquisitionSys": win.config.acquisitionSys,
        "sampleRate": win.config.srate,
        "chnNUM": win.config.chnNUM,
        "ITR": itr_value,
        "accuracy": accuracy,
        "timeAndDate": formatted_date_time,
        "monitor": win.monitorComboBox.itemText(win.config.windowIndex),
        "run_mode": win.config.MODE,
        "sync_mode": win.config.sync_mode,
        "feature_extraction": win.config.feature_algo,
        "num_of_blocks": win.config.blockNUM,
        "data_saved_path ": win.config.resultPath,
        "offline_image": os.path.join(win.config.resultPath, win.config.personName, 'images', f'{win.config.prefix_with_time}offline.png'),
        "total_time": win.total_time_label.text().replace("\n", " "),
        "keyboard_name": win.config.keyType,
        "keyboard_processing_table": convert_qtablewidget_to_list(win.keyboard_processing_table),
    }


    # Create the report with a timestamp in the filename
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_filename = f"report_{current_time}.pdf"
    address = os.path.join(win.config.resultPath, win.config.personName, 'report', report_filename)
    create_pdf_report(data, address)


    if platform.system() == 'Linux':
        subprocess.call(["xdg-open", address])
    elif platform.system() == 'Windows':
        os.startfile(address)
    elif platform.system() == 'Darwin':
        subprocess.call(["open", address])
    else:
        print(f"Could not open the PDF: unsupported platform '{platform.system()}'.")
    
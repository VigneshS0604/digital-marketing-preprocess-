from flask import Flask, render_template, request, send_file
import pandas as pd
import os
import tempfile

app = Flask(__name__)

# Define the mapping of weekdays
weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# Function to format dates
def format_date(date_obj):
    return f"{date_obj.day} {date_obj.strftime('%b')} ({weekdays[date_obj.weekday()]})"

# Preprocessing function
def preprocess_data(file):
    dataset = pd.read_excel(file)

    # Format date columns
    date_columns = ['Day', 'Reporting starts', 'Reporting ends']
    for col in date_columns:
        dataset[col] = pd.to_datetime(dataset[col]).apply(format_date)

    # Rename columns
    dataset.rename(columns={'Results': 'No of leads', 'CTR (link click-through rate)': 'CTR', 'Amount spent (INR)': 'AD Spend'}, inplace=True)

    # Fill missing values with 0
    dataset.fillna(0, inplace=True)

    # Calculate 'Cost Per Lead'
    dataset['Cost Per Lead'] = dataset['AD Spend'] / dataset['No of leads']

    # Calculate 'Member passed' and 'LP Conversion'
    dataset['Member passed'] = (dataset['Landing page views'] / dataset['Link clicks']) * 100
    dataset['LP Conversion'] = (dataset['No of leads'] / dataset['Landing page views']) * 100

    # Replace infinite values with NaN
    dataset.replace([float('inf'), -float('inf')], pd.NA, inplace=True)
    # Fill missing values with 0
    dataset.fillna(0, inplace=True)
    # Convert 'LP Conversion' and 'CTR' to percentage and format
    dataset['LP Conversion'] = dataset['LP Conversion'].map(lambda x: f"{x:.2f}%" )
    dataset['CTR'] = dataset['CTR'].map(lambda x: f"{x:.2f}%")

    # Reorder and keep selected columns
    columns_to_keep = ['Day', 'Campaign name', 'AD Spend', 'No of leads', 'Cost Per Lead',
                       'CTR', 'Landing page views', 'Member passed', 'LP Conversion']
    dataset = dataset[columns_to_keep]

    return dataset

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            filename = file.filename
            temp_dir = tempfile.gettempdir()  # Get the temporary directory
            temp_file_path = os.path.join(temp_dir, filename)
            file.save(temp_file_path)
            processed_data = preprocess_data(temp_file_path)
            temp_processed_file_path = os.path.join(temp_dir, 'processed_data.xlsx')
            processed_data.to_excel(temp_processed_file_path, index=False)
            return render_template('download.html', filename='processed_data.xlsx')
    return render_template('index.html', message="No file uploaded.")

@app.route('/download', methods=['GET'])
def download():
    filename = request.args.get('filename')
    if filename:
        temp_dir = tempfile.gettempdir()  # Get the temporary directory
        path = os.path.join(temp_dir, filename)
        return send_file(path, as_attachment=True)
    else:
        return "File not found."

@app.route('/filter', methods=['POST'])
def filter_data():
    if request.method == 'POST':
        day = request.form['day']
        if day:
            # Assume dataset is loaded from a file or some other source
            temp_dir = tempfile.gettempdir()  # Get the temporary directory
            dataset = pd.read_excel(os.path.join(temp_dir, 'processed_data.xlsx'))
            filtered_data = dataset[dataset['Day'].str.endswith(day)]
            if not filtered_data.empty:
                temp_file_path = os.path.join(temp_dir, f'filtered_data_{day}.xlsx')
                filtered_data.to_excel(temp_file_path, index=False)
                return render_template('filter.html', message=f"Filtered dataset for {day} has been saved successfully.", filename=f'filtered_data_{day}.xlsx')
            else:
                return render_template('filter.html', message="No data found for the specified day.")
    return render_template('index.html', message="Please enter a day to filter.")

@app.route('/download-filtered/<filename>', methods=['GET'])
def download_filtered(filename):
    temp_dir = tempfile.gettempdir()  # Get the temporary directory
    path = os.path.join(temp_dir, filename)
    return send_file(path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)

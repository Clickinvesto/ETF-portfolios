import dash_mantine_components as dmc
import csv
from src.Dash.utils.functions import get_icon
import base64
from io import StringIO
from datetime import datetime


def check_first_column_date_format(potential_file, date_format="%d/%m/%Y"):
    try:
        potential_file.seek(0)  # Ensure we start reading from the beginning
        reader = csv.reader(potential_file)
        headers = next(reader)  # Read the first row (headers)
        for row in reader:
            if not row:  # Skip empty rows
                continue
            date_str = row[0]  # Get the first column value
            try:
                # Try to parse the date string using the expected format
                datetime.strptime(date_str, date_format)
            except ValueError:
                # If parsing fails, print the problematic date string and return False
                print(f"Date format mismatch: {date_str}")
                return False

        # If all dates match the format, return True
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


def check_delimiter(potential_file, expected_delimiter=","):

    sample = potential_file.read(1024)
    potential_file.seek(0)
    # Use the csv Sniffer to detect the dialect
    sniffer = csv.Sniffer()
    dialect = sniffer.sniff(sample)

    # Check if the delimiter is the expected one
    if dialect.delimiter == expected_delimiter:
        return True
    else:
        return False


def is_utf8(content_string):
    try:
        decoded_content = base64.b64decode(content_string)
        decoded_string = decoded_content.decode("utf-8")
        return True
    except:
        return False

        # ("Date (month)")


def check_column_header(potential_file, position=0, expected_header="Date"):
    try:
        potential_file.seek(0)
        reader = csv.reader(potential_file)
        headers = next(reader)  # Read the first row (header)
        if headers[position] == expected_header:
            return True
        else:
            return False
    except:
        return False


def create_check_list(file_name, file_content):
    tests = [False, False, False, False, False, False, False]
    tests[0] = True if file_name.split(".")[0] == "Series" else False
    tests[1] = True if file_name.split(".")[-1] == "csv" else False
    tests[2] = is_utf8(file_content)
    if tests[2]:
        decoded_content = base64.b64decode(file_content)
        decoded_string = decoded_content.decode("utf-8")
        potential_file = StringIO(decoded_string)
        tests[3] = check_delimiter(potential_file)
        tests[4] = check_column_header(potential_file)
        tests[5] = check_first_column_date_format(potential_file)
        tests[6] = check_column_header(potential_file, position=1, expected_header="RI")
    text = [
        "The file is named: Series",
        "The file is a csv",
        "The file is saved in UTF-8",
        "The csv is delimiter is , (comma)",
        "The first column is named: Date",
        "The date format should be: %d/%m/%Y e.g. 01/08/1980",
        "The second column is named: RI",
    ]
    disable_upload = any(value is False for value in tests)
    list_content = [
        (
            dmc.ListItem(text[index])
            if test
            else dmc.ListItem(
                text[index],
                icon=dmc.ThemeIcon(
                    get_icon(icon="material-symbols:error-outline", height=16),
                    radius="xl",
                    color="red",
                    size=24,
                ),
            )
        )
        for index, test in enumerate(tests)
    ]

    return disable_upload, list_content

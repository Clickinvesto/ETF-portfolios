import json
import yaml
import os
import datetime
from flask import current_app
import pandas as pd


def format_date(input_date, input_format="%Y-%m-%d", return_format="%Y-%m-%d %H:%M:%S"):
    if isinstance(input_date, pd.Series):
        if not isinstance(input_date[0], pd.Timestamp):
            input_date = pd.to_datetime(input_date, format=input_format)
        input_date = input_date.dt.strftime(return_format)
        return input_date

    if isinstance(input_date, str):
        datetime_value = datetime.datetime.strptime(input_date, input_format)
        datetime_value = datetime_value.strftime(return_format)
        return datetime_value
    else:
        input_date = input_date.strftime(return_format)
        return input_date


class S3Mixin:
    def get_data_file(self, path):
        data_file = (
            current_app.config["S3_CLIENT"]
            .Object(current_app.config["S3_BUCKET"], path)
            .get()
        )
        return data_file["Body"]

    def upload_files_to_s3(self, file_paths, folder_name):
        s3_client = current_app.config["S3_CLIENT"]
        bucket_name = current_app.config["S3_BUCKET"]
        for file_path in file_paths:
            # Ensure the folder name ends with a slash
            if not folder_name.endswith("/"):
                folder_name += "/"

            # Extract the filename from the file path
            file_name = os.path.basename(file_path)

            # Create the destination key for the file in the S3 bucket
            s3_key = folder_name + file_name

            try:
                # Upload the file to S3
                s3_client.Bucket(bucket_name).upload_file(file_path, s3_key)
                print(f"Successfully uploaded {file_path} to {s3_key}")
            except Exception as e:
                print(f"Failed to upload {file_path} to {s3_key}: {e}")

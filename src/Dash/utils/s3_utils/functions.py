def upload_files_to_s3(s3_client, bucket_name, file_paths, folder_name):
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


def list_s3_files(s3_client, bucket_name):
    # List all the objects in the specified bucket
    response = s3_client.meta.client.list_objects_v2(Bucket=bucket_name)

    # Check if the bucket has any contents
    if "Contents" in response:
        # Iterate through the list of objects and print their keys (file names)
        for obj in response["Contents"]:
            print(obj["Key"])
    else:
        print(f"The bucket {bucket_name} is empty.")

    upload_files_to_s3(
        s3_client,
        bucket_name,
        [
            "/home/simon/Documents/Pure_Inference/Kunden/Andres/dashboard/src/Dash/data/countries.csv",
            "/home/simon/Documents/Pure_Inference/Kunden/Andres/dashboard/src/Dash/data/new_result.csv",
            "/home/simon/Documents/Pure_Inference/Kunden/Andres/dashboard/src/Dash/data/Series.csv",
            "/home/simon/Documents/Pure_Inference/Kunden/Andres/dashboard/src/Dash/data/result.csv",
        ],
        "data",
    )
    list_s3_files(s3_client, bucket_name)

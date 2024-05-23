from flask import redirect, abort
from flask_admin.babel import gettext

from flask_admin.contrib.fileadmin import BaseFileAdmin


class S3Storage(object):
    """
    Storage object representing files on an Amazon S3 bucket.

    Usage::

        from flask_admin.contrib.fileadmin import BaseFileAdmin
        from flask_admin.contrib.fileadmin.s3 import S3Storage

        class MyS3Admin(BaseFileAdmin):
            # Configure your class however you like
            pass

        fileadmin_view = MyS3Admin(storage=S3Storage(...))

    """

    def __init__(self, s3client, bucket_name):
        """
        Constructor

            :param bucket_name:
                Name of the bucket that the files are on.

            :param region:
                Region that the bucket is located

            :param aws_access_key_id:
                AWS Access Key ID

            :param aws_secret_access_key:
                AWS Secret Access Key

        Make sure the credentials have the correct permissions set up on
        Amazon or else S3 will return a 403 FORBIDDEN error.
        """

        if not s3client:
            raise ValueError(
                "Could not import boto. You can install boto by "
                "using pip install boto"
            )

        self.bucket = s3client.Bucket(bucket_name)
        self.separator = "/"

    def get_files(self, path, directory):
        # Updated method for listing files using boto3
        if path == "":
            path = "data/"

        def _strip_path(name, path):
            if name.startswith(path):
                return name[len(path) :]
            return name

        files = []
        directories = set()
        if path and not path.endswith(self.separator):
            path += self.separator

        # Correctly use the Delimiter parameter in the filter method
        response = self.bucket.meta.client.list_objects_v2(
            Bucket=self.bucket.name, Prefix=path, Delimiter=self.separator
        )
        for content in response.get("Contents", []):
            last_modified_timestamp = int(content["LastModified"].timestamp())
            if content["Key"].split("/")[-1] != "":
                files.append(
                    (
                        content["Key"].split("/")[-1],
                        content["Key"],
                        False,
                        content["Size"],
                        last_modified_timestamp,
                    )
                )
        for prefix in response.get("CommonPrefixes", []):
            dir_name = prefix["Prefix"][
                len(path) : -1
            ]  # Strip base path and trailing separator
            if dir_name != "":
                directories.add((dir_name, prefix["Prefix"], True, 0, 0))

        return list(directories) + files

    def _get_bucket_list_prefix(self, path):
        parts = path.split(self.separator)
        if len(parts) == 1:
            search = ""
        else:
            search = self.separator.join(parts[:-1]) + self.separator

        return search

    def _get_path_keys(self, path):
        search = self._get_bucket_list_prefix(path)
        keys_set = set()
        # Use the objects.filter method to list objects based on the prefix
        for obj in self.bucket.objects.filter(Prefix=search):
            keys_set.add(obj.key)
        return keys_set

    def is_dir(self, path):
        keys = self._get_path_keys(path)
        return path + self.separator in keys

    def path_exists(self, path):
        # Check if bath path exists and return the keys
        if path == "":
            return True
        keys = self._get_path_keys(path)
        return path in keys or (path + self.separator) in keys

    def get_base_path(self):
        return ""

    def get_breadcrumbs(self, path):
        accumulator = []
        breadcrumbs = []
        for n in path.split(self.separator):
            accumulator.append(n)
            breadcrumbs.append((n, self.separator.join(accumulator)))
        return breadcrumbs

    def send_file(self, file_path):
        """
        Generates a secure URL to download a file from S3 and redirects the user to it.
        """
        try:
            # Attempt to generate a URL for the specified file
            key = self.bucket.Object(file_path)
            url = key.meta.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket.name, "Key": file_path},
                ExpiresIn=3600,
            )
            return redirect(url)
        except self.bucket.meta.client.exceptions.NoSuchKey:
            abort(404)
        except Exception as e:
            abort(500)

    def save_file(self, path, file_data):

        extra_args = {"ContentType": file_data.content_type}
        self.bucket.upload_fileobj(
            Fileobj=file_data.stream,  # File-like object to upload
            Key=path,  # Key under which the file should be stored in the bucket
            ExtraArgs=extra_args,  # Additional arguments, including headers
        )

    def delete_tree(self, directory):
        # Ensure the directory path is correctly formatted
        prefix = directory.rstrip(self.separator) + self.separator

        # List all objects under the directory
        objects_to_delete = list(self.bucket.objects.filter(Prefix=prefix))

        # Optionally, check if the directory is "empty" (has no objects)
        if not objects_to_delete:
            print(f"The directory '{directory}' is empty or does not exist.")
            return

        # Delete the objects
        self.bucket.delete_objects(
            Delete={"Objects": [{"Key": obj.key} for obj in objects_to_delete]}
        )

    def delete_file(self, file_path):
        print(file_path)
        obj = self.bucket.Object(file_path)
        obj.delete()

    def make_dir(self, path, directory):
        dir_path = (
            self.separator.join([path.rstrip(self.separator), directory]).rstrip(
                self.separator
            )
            + self.separator
        )

        # Use the bucket to put an empty object with the directory path key
        self.bucket.put_object(Key=dir_path, Body=b"")

    def _check_empty_directory(self, path):
        if not self._is_directory_empty(path):
            raise ValueError(gettext("Cannot operate on non empty " "directories"))
        return True

    def rename_path(self, src, dst):
        if self.is_dir(src):
            self._check_empty_directory(src)
            src += self.separator
            dst += self.separator
        # Construct the full source object reference
        copy_source = {"Bucket": self.bucket.name, "Key": src}

        # Copy the source object to the new destination
        self.bucket.copy(copy_source, dst)

        # After copying, delete the original source object
        self.delete_file(src)

    def _is_directory_empty(self, path):
        keys = self._get_path_keys(path + self.separator)
        return len(keys) == 1

    def read_file(self, path):
        # Using the bucket object to get the object specified by path
        obj = self.bucket.Object(path)

        # Getting the object's content
        response = obj.get()
        data = response["Body"].read()

        # Assuming the content is a string, decode it from bytes to a string
        return data.decode("utf-8")

    def write_file(self, path, content):
        obj = self.bucket.Object(path)

        # Check if 'content' is a file-like object (has an attribute 'read')
        if hasattr(content, "read"):
            # 'content' is a file-like object, use upload_fileobj
            obj.upload_fileobj(content)
        elif isinstance(content, (str, bytes)):
            # 'content' is a string or bytes, use put
            # If 'content' is a string, encode it to bytes
            if isinstance(content, str):
                content = content.encode("utf-8")
            obj.put(Body=content)
        else:
            # Raise an error if 'content' is neither file-like, bytes, nor string
            raise ValueError(
                "Unsupported content type. Content must be a file-like object, string, or bytes."
            )


class S3FileAdmin(BaseFileAdmin):
    """
    Simple Amazon Simple Storage Service file-management interface.

        :param bucket_name:
            Name of the bucket that the files are on.

        :param region:
            Region that the bucket is located

        :param aws_access_key_id:
            AWS Access Key ID

        :param aws_secret_access_key:
            AWS Secret Access Key

    Sample usage::

        from flask_admin import Admin
        from flask_admin.contrib.fileadmin.s3 import S3FileAdmin

        admin = Admin()

        admin.add_view(S3FileAdmin('files_bucket', 'us-east-1', 'key_id', 'secret_key')
    """

    def __init__(self, s3client, bucket_name, *args, **kwargs):
        storage = S3Storage(s3client, bucket_name)
        super(S3FileAdmin, self).__init__(*args, storage=storage, **kwargs)

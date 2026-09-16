from hashlib import md5
from urllib.parse import quote
from uuid import UUID, uuid4

from botocore.exceptions import ClientError
from documentservice.rfc6266 import build_header
from documentservice.storage import (
    ContentUploaded,
    HashInvalid,
    KeyNotFound,
    StorageRedirect,
    get_filename,
)

EXPIRES_IN = 300
# a missing bucket is a misconfiguration, not a missing document - let it propagate
NOT_FOUND_CODES = ("404", "NoSuchKey")


def key_path(uuid):
    return "/".join([format(i, "x") for i in UUID(uuid).fields])


def content_disposition(filename):
    # build_header() returns iso-8859-1 bytes; boto3 wants a str header value
    header = build_header(filename, filename_compat=quote(filename.encode("utf-8")))
    return header.decode("iso-8859-1")


def file_md5(in_file):
    digest = md5()
    for chunk in iter(lambda: in_file.read(8192), b""):
        digest.update(chunk)
    in_file.seek(0)
    return digest.hexdigest()


class S3Storage:
    def __init__(self, client, bucket):
        self.client = client
        self.bucket = bucket

    def register(self, md5hash):
        uuid = uuid4().hex
        self.client.put_object(
            Bucket=self.bucket, Key=key_path(uuid), Body=b"", Metadata={"hash": md5hash}
        )
        return uuid

    def upload(self, post_file, uuid=None):
        filename = get_filename(post_file.filename)
        content_type = post_file.type
        in_file = post_file.file
        if uuid is None:
            uuid = uuid4().hex
            key = key_path(uuid)
        else:
            key = self.__key_path(uuid)
            head = self.__head(uuid, key)
            if head["ContentLength"] != 0:
                raise ContentUploaded(uuid)
            md5hash = head["Metadata"]["hash"]
            if file_md5(in_file) != md5hash[4:]:
                raise HashInvalid(md5hash)
        response = self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=in_file,
            ContentType=content_type,
            ContentDisposition=content_disposition(filename),
        )
        return uuid, "md5:" + response["ETag"].strip('"'), content_type, filename

    def get(self, uuid):
        key = uuid if "/" in uuid else self.__key_path(uuid)
        url = self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=EXPIRES_IN,
        )
        raise StorageRedirect(url)

    @staticmethod
    def __key_path(uuid):
        try:
            return key_path(uuid)
        except ValueError:
            raise KeyNotFound(uuid)

    def __head(self, uuid, key):
        try:
            return self.client.head_object(Bucket=self.bucket, Key=key)
        except ClientError as err:
            if err.response["Error"]["Code"] in NOT_FOUND_CODES:
                raise KeyNotFound(uuid)
            raise

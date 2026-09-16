import boto3

from .storage import S3Storage

REQUIRED_SETTINGS = ("s3.access_key", "s3.secret_key", "s3.bucket", "s3.region")


def includeme(config):
    settings = config.registry.settings
    missing = [name for name in REQUIRED_SETTINGS if name not in settings]
    if missing:
        raise ValueError("{} are required".format(", ".join(missing)))
    client = boto3.client(
        "s3",
        region_name=settings["s3.region"],
        aws_access_key_id=settings["s3.access_key"],
        aws_secret_access_key=settings["s3.secret_key"],
    )
    config.registry.storage = S3Storage(client, settings["s3.bucket"])

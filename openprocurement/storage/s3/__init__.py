from boto.s3 import connect_to_region
from openprocurement.storage.s3.storage import S3Storage


def includeme(config):
    settings = config.registry.settings
    print("settings")
    print(settings)
    if (
        's3.access_key' in settings
        and 's3.access_key' in settings
        and 's3.secret_key' in settings
        and 's3.bucket' in settings
    ):
        connection = connect_to_region(
            settings['s3.region'],
            aws_access_key_id=settings['s3.access_key'],
            aws_secret_access_key=settings['s3.secret_key']
        )
        config.registry.storage = S3Storage(connection, settings['s3.bucket'])
    else:
        raise ValueError("s3.access_key, s3.secret_key, s3.bucket are required ")

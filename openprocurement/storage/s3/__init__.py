from boto.s3.connection import S3Connection
from openprocurement.storage.s3.storage import S3Storage


def includeme(config):
    settings = config.registry.settings
    if 's3.access_key' in settings and 's3.secret_key' in settings and 's3.bucket' in settings:
        # S3 connection
        connection = S3Connection(settings['s3.access_key'], settings['s3.secret_key'])
        bucket_name = settings['s3.bucket']
        config.registry.storage = S3Storage(connection, bucket_name)
    else:
        raise ValueError("s3.access_key, s3.secret_key, s3.bucket are required ")

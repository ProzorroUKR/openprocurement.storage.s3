import os
import unittest

import boto3
import webtest
from moto import mock_aws

BUCKET = "test"
REGION = "eu-central-1"


class BaseWebTest(unittest.TestCase):
    """Base Web Test to test storage_s3."""

    def setUp(self):
        self.mock_aws = mock_aws()
        self.mock_aws.start()
        self.addCleanup(self.mock_aws.stop)

        boto3.client("s3", region_name=REGION).create_bucket(
            Bucket=BUCKET, CreateBucketConfiguration={"LocationConstraint": REGION}
        )

        self.app = webtest.TestApp(
            "config:tests.ini", relative_to=os.path.dirname(__file__)
        )
        self.app.authorization = ("Basic", ("broker", "broker"))
        self.storage = self.app.app.registry.storage

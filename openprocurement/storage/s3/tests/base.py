# -*- coding: utf-8 -*-
from boto.utils import compute_md5
from boto.utils import find_matching_headers
from boto.utils import merge_headers_by_name
from hashlib import md5
import boto
import copy
import os
import unittest
import webtest

NOT_IMPL = None


class MockAcl(object):

    def __init__(self, parent=NOT_IMPL):
        pass

    def startElement(self, name, attrs, connection):
        pass

    def endElement(self, name, value, connection):
        pass

    def to_xml(self):
        return '<mock_ACL_XML/>'


class MockKey(object):

    def __init__(self, bucket=None, name=None):
        self.bucket = bucket
        self.name = name
        self.data = None
        self.etag = None
        self.size = None
        self.closed = True
        self.content_encoding = None
        self.content_language = None
        self.content_type = None
        self.last_modified = 'Wed, 06 Oct 2010 05:11:54 GMT'
        self.BufferSize = 8192
        self.metadata = {}

    def set_contents_from_file(self, fp, headers=None, replace=NOT_IMPL,
                               cb=NOT_IMPL, num_cb=NOT_IMPL,
                               policy=NOT_IMPL, md5=NOT_IMPL,
                               res_upload_handler=NOT_IMPL):
        self.data = fp.read()
        self.set_etag()
        self.size = len(self.data)
        self._handle_headers(headers)

    def set_contents_from_string(self, s, headers=NOT_IMPL, replace=NOT_IMPL,
                                 cb=NOT_IMPL, num_cb=NOT_IMPL, policy=NOT_IMPL,
                                 md5=NOT_IMPL, reduced_redundancy=NOT_IMPL):
        self.data = copy.copy(s.encode('utf-8'))
        self.set_etag()
        self.size = len(s)
        self._handle_headers(headers)

    def set_acl(self, acl_str, headers=None):
        pass

    def _handle_headers(self, headers):
        if not headers:
            return
        if find_matching_headers('Content-Encoding', headers):
            self.content_encoding = merge_headers_by_name('Content-Encoding',
                                                          headers)
        if find_matching_headers('Content-Type', headers):
            self.content_type = merge_headers_by_name('Content-Type', headers)
        if find_matching_headers('Content-Language', headers):
            self.content_language = merge_headers_by_name('Content-Language',
                                                          headers)

    def set_etag(self):
        """
        Set etag attribute by generating hex MD5 checksum on current
        contents of mock key.
        """
        m = md5()
        m.update(self.data)
        hex_md5 = m.hexdigest()
        self.etag = hex_md5

    def set_metadata(self, name, value):
        # Ensure that metadata that is vital to signing is in the correct
        # case. Applies to ``Content-Type`` & ``Content-MD5``.
        if name.lower() == 'content-type':
            self.metadata['Content-Type'] = value
        elif name.lower() == 'content-md5':
            self.metadata['Content-MD5'] = value
        else:
            self.metadata[name] = value

    def set_remote_metadata(self, metadata_plus, metadata_minus, preserve_acl,
                            headers=None):
        src_bucket = self.bucket
        metadata = self.metadata
        metadata.update(metadata_plus)
        for h in metadata_minus:
            if h in metadata:
                del metadata[h]
        rewritten_metadata = {}
        for h in metadata:
            if (h.startswith('x-goog-meta-') or h.startswith('x-amz-meta-')):
                rewritten_h = (h.replace('x-goog-meta-', '')
                               .replace('x-amz-meta-', ''))
            else:
                rewritten_h = h
            rewritten_metadata[rewritten_h] = metadata[h]
        metadata = rewritten_metadata
        src_bucket.copy_key(self.name, self.bucket.name, self.name,
                            metadata=metadata, preserve_acl=preserve_acl,
                            headers=headers)

    def copy(self, dst_bucket_name, dst_key, metadata=NOT_IMPL,
             reduced_redundancy=NOT_IMPL, preserve_acl=NOT_IMPL):
        dst_bucket = self.bucket.connection.get_bucket(dst_bucket_name)
        return dst_bucket.copy_key(dst_key, self.bucket.name, self.name, metadata)

    def get_metadata(self, name):
        if name.lower() == 'content-type':
            return self.metadata['Content-Type']
        elif name.lower() == 'content-md5':
            return self.metadata['Content-MD5']
        else:
            return self.metadata[name]

    def compute_md5(self, fp):
        """
        :type fp: file
        :param fp: File pointer to the file to MD5 hash.  The file pointer
                   will be reset to the beginning of the file before the
                   method returns.
        :rtype: tuple
        :return: A tuple containing the hex digest version of the MD5 hash
                 as the first element and the base64 encoded version of the
                 plain digest as the second element.
        """
        tup = compute_md5(fp)
        # Returned values are MD5 hash, base64 encoded MD5 hash, and file size.
        # The internal implementation of compute_md5() needs to return the
        # file size but we don't want to return that value to the external
        # caller because it changes the class interface (i.e. it might
        # break some code) so we consume the third tuple value here and
        # return the remainder of the tuple to the caller, thereby preserving
        # the existing interface.
        self.size = tup[2]
        return tup[0:2]


class MockBucket(object):

    def __init__(self, connection=None, name=None, key_class=NOT_IMPL):
        self.name = name
        self.keys = {}
        self.acls = {name: MockAcl()}
        # default object ACLs are one per bucket and not supported for keys
        self.def_acl = MockAcl()
        self.subresources = {}
        self.connection = connection
        self.logging = False

    def new_key(self, key_name=None):
        mock_key = MockKey(self, key_name)
        self.keys[key_name] = mock_key
        self.acls[key_name] = MockAcl()
        return mock_key

    def __contains__(self, key_name):
        return not (self.get_key(key_name) is None)

    def get_key(self, key_name, headers=NOT_IMPL, version_id=NOT_IMPL):
        # Emulate behavior of boto when get_key called with non-existent key.
        if key_name not in self.keys:
            return None
        return self.keys[key_name]

    def copy_key(self, new_key_name, src_bucket_name,
                 src_key_name, metadata=NOT_IMPL, src_version_id=NOT_IMPL,
                 storage_class=NOT_IMPL, preserve_acl=NOT_IMPL,
                 encrypt_key=NOT_IMPL, headers=NOT_IMPL, query_args=NOT_IMPL):
        src_key = self.connection.get_bucket(src_bucket_name).get_key(src_key_name)
        new_key = self.new_key(key_name=new_key_name)
        new_key.data = copy.copy(src_key.data)
        new_key.size = len(new_key.data)
        return new_key


class MockProvider(object):

    def __init__(self, provider):
        self.provider = provider

    def get_provider_name(self):
        return self.provider


class MockConnection(object):

    def __init__(self, aws_access_key_id=NOT_IMPL,
                 aws_secret_access_key=NOT_IMPL, is_secure=NOT_IMPL,
                 port=NOT_IMPL, proxy=NOT_IMPL, proxy_port=NOT_IMPL,
                 proxy_user=NOT_IMPL, proxy_pass=NOT_IMPL,
                 host=NOT_IMPL, debug=NOT_IMPL,
                 https_connection_factory=NOT_IMPL,
                 calling_format=NOT_IMPL,
                 path=NOT_IMPL, provider='s3',
                 bucket_class=NOT_IMPL):
        self.buckets = {}
        self.provider = MockProvider(provider)

    def create_bucket(self, bucket_name, headers=NOT_IMPL, location=NOT_IMPL,
                      policy=NOT_IMPL, storage_class=NOT_IMPL):
        if bucket_name in self.buckets:
            raise boto.exception.StorageCreateError(
                409, 'BucketAlreadyOwnedByYou',
                "<Message>Your previous request to create the named bucket "
                "succeeded and you already own it.</Message>")
        mock_bucket = MockBucket(name=bucket_name, connection=self)
        self.buckets[bucket_name] = mock_bucket
        return mock_bucket

    def get_bucket(self, bucket_name, validate=NOT_IMPL, headers=NOT_IMPL):
        if bucket_name not in self.buckets:
            raise boto.exception.StorageResponseError(404, 'NoSuchBucket', 'Not Found')
        return self.buckets[bucket_name]

    def get_all_buckets(self, headers=NOT_IMPL):
        return self.buckets.itervalues()

    def generate_url(self, expires_in, method, bucket='', key='', headers=None,
                     query_auth=True, force_http=False, response_headers=None,
                     expires_in_absolute=False, version_id=None):
        return 'http://s3/{}/{}'.format(bucket, key)


class BaseWebTest(unittest.TestCase):

    """Base Web Test to test openprocurement.api.

    It setups the database before each test and delete it after.
    """

    def setUp(self):
        self.app = webtest.TestApp(
            "config:tests.ini", relative_to=os.path.dirname(__file__))
        self.app.authorization = ('Basic', ('broker', 'broker'))
        connection = MockConnection()
        connection.create_bucket(self.app.app.registry.storage.bucket)
        self.app.app.registry.storage.connection = connection

    def tearDown(self):
        pass

# -*- coding: utf-8 -*-

import unittest
from hashlib import md5
from openprocurement.storage.s3.tests.base import BaseWebTest


class SimpleTest(BaseWebTest):

    def test_root(self):
        response = self.app.get('/')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'text/plain')
        self.assertEqual(response.body, b'')

    def test_register_get(self):
        response = self.app.get('/register', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'text/plain')

    def test_upload_get(self):
        response = self.app.get('/upload', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'text/plain')

    def test_upload_file_get(self):
        response = self.app.get('/upload/uuid', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'text/plain')

    def test_register_invalid(self):
        url = '/register'
        response = self.app.post(url, 'data', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {'description': 'Not Found', 'location': 'body', 'name': 'hash'}
        ])

        response = self.app.post(url, {'not_md5': 'hash'}, status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {'description': 'Not Found', 'location': 'body', 'name': 'hash'}
        ])

        response = self.app.post(url, {'hash': 'hash'}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {'description': ['Hash type is not supported.'], 'name': 'hash', 'location': 'body'}
        ])

        response = self.app.post(url, {'hash': 'md5:hash'}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {'description': ['Hash value is wrong length.'], 'name': 'hash', 'location': 'body'}
        ])

        response = self.app.post(url, {'hash': 'md5:' + 'o' * 32}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {'description': ['Hash value is not hexadecimal.'], 'name': 'hash', 'location': 'body'}
        ])

    def test_register_post(self):
        response = self.app.post('/register', {'hash': 'md5:' + '0' * 32, 'filename': 'file.txt'})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        self.assertIn('http://localhost/upload/', response.json['upload_url'])

    def test_upload_invalid(self):
        url = '/upload'
        response = self.app.post(url, 'data', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {'description': 'Not Found', 'location': 'body', 'name': 'file'}
        ])

    def test_upload_post(self):
        response = self.app.post('/upload', upload_files=[('file', 'file.txt', b'content')])
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertIn('http://localhost/get/', response.json['get_url'])

    def test_upload_file_invalid(self):
        url = '/upload/uuid'
        response = self.app.post(url, 'data', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {'description': 'Not Found', 'location': 'body', 'name': 'file'}
        ])

        response = self.app.post(url, upload_files=[('file', 'file.doc', b'content')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {'description': 'Not Found', 'name': 'Signature', 'location': 'url'}
        ])

        response = self.app.post(url + '?KeyID=test', upload_files=[('file', 'file.doc', b'content')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {'description': 'Key Id does not exist', 'name': 'KeyID', 'location': 'url'}
        ])

        response = self.app.post(url + '?Signature=', upload_files=[('file', 'file.doc', b'content')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {'description': 'Signature invalid', 'name': 'Signature', 'location': 'url'}
        ])

    def test_upload_file_md5(self):
        response = self.app.post('/register', {'hash': 'md5:' + '0' * 32, 'filename': 'file.txt'})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        self.assertIn('http://localhost/upload/', response.json['upload_url'])

        response = self.app.post(response.json['upload_url'], upload_files=[('file', 'file.doc', b'content')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {'description': 'Invalid checksum', 'name': 'file', 'location': 'body'}
        ])

    def test_upload_file_post(self):
        content = b'content'
        md5hash = 'md5:' + md5(content).hexdigest()
        response = self.app.post('/register', {'hash': md5hash, 'filename': 'file.txt'})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        self.assertIn('http://localhost/upload/', response.json['upload_url'])
        upload_url = response.json['upload_url']

        response = self.app.post(upload_url, upload_files=[('file', 'file.txt', b'content')])
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertIn('http://localhost/get/', response.json['get_url'])

        response = self.app.post(upload_url, upload_files=[('file', 'file.txt', b'content')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'], [
            {'description': 'Content already uploaded', 'name': 'doc_id', 'location': 'url'}
        ])

        response = self.app.post(upload_url.replace('?', 'a?'), upload_files=[('file', 'file.doc', b'content')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {'description': 'Signature does not match', 'name': 'Signature', 'location': 'url'}
        ])

    def test_get_invalid(self):
        response = self.app.get('/get/uuid', status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {'description': 'Not Found', 'name': 'Signature', 'location': 'url'}
        ])

        response = self.app.get('/get/uuid?KeyID=test', status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {'description': 'Key Id does permit to get private document', 'name': 'KeyID', 'location': 'url'}
        ])

        response = self.app.get('/get/uuid?Expires=1', status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {'description': 'Request has expired', 'name': 'Expires', 'location': 'url'}
        ])

        response = self.app.get('/get/uuid?Expires=2000000000', status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {'description': 'Not Found', 'name': 'Signature', 'location': 'url'}
        ])

        response = self.app.get('/get/uuid?Expires=2000000000&Signature=', status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {'description': 'Signature invalid', 'name': 'Signature', 'location': 'url'}
        ])

        response = self.app.get('/get/uuid?Expires=2000000000&Signature=&KeyID=test', status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {'description': 'Key Id does not exist', 'name': 'KeyID', 'location': 'url'}
        ])

        response = self.app.post('/upload', upload_files=[('file', 'file.txt', b'')])
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertIn('http://localhost/get/', response.json['get_url'])

        response = self.app.get(response.json['get_url'])
        self.assertEqual(response.status, '302 Found')

    def test_file_get(self):
        md5hash = 'md5:' + md5(b'content').hexdigest()
        response = self.app.post('/register', {'hash': md5hash, 'filename': 'file.txt'})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        self.assertIn('http://localhost/upload/', response.json['upload_url'])

        response = self.app.post(response.json['upload_url'], upload_files=[('file', 'file.txt', b'content')])
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertIn('http://localhost/get/', response.json['get_url'])

        response = self.app.get(response.json['get_url'])
        self.assertEqual(response.status, '302 Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertIn('http://s3/test/', response.json)

    def test_get(self):
        response = self.app.post('/upload', upload_files=[('file', 'file.txt', b'content')])
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertIn('http://localhost/get/', response.json['get_url'])

        response = self.app.get(response.json['get_url'])
        self.assertEqual(response.status, '302 Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertIn('http://s3/test/', response.json)

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(SimpleTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')

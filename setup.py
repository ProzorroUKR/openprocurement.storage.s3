from setuptools import setup, find_packages
import os

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'README.md')) as f:
    README = f.read()

version = '1.0.6'

requires = [
    'boto',
    'rfc6266',
    'openprocurement.documentservice>=1.4.0',
]
test_requires = requires + [
    'pytest',
    'pytest-cov',
    'python-coveralls',
    'mock',
    'webtest',
]
docs_requires = requires + [
    'sphinxcontrib-httpdomain',
]
entry_points = {
    'openprocurement.documentservice.plugins': [
        's3 = openprocurement.storage.s3:includeme'
    ]
}

setup(name='openprocurement.storage.s3',
      version=version,
      description="S3 storage for OpenProcurement document service",
      long_description=README,
      classifiers=[
          "Framework :: Pylons",
          "License :: OSI Approved :: Apache Software License",
          "Programming Language :: Python",
          "Topic :: Internet :: WWW/HTTP",
          "Topic :: Internet :: WWW/HTTP :: WSGI :: Application"
      ],
      keywords='web services',
      author='Quintagroup, Ltd.',
      author_email='info@quintagroup.com',
      url='https://github.com/ProzorroUKR/openprocurement.storage.s3',
      license='Apache License 2.0',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['openprocurement', 'openprocurement.storage'],
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      tests_require=test_requires,
      extras_require={'test': test_requires, 'docs': docs_requires},
      test_suite="openprocurement.storage.s3.tests.main.suite",
      entry_points=entry_points)

Backend for https://github.com/ProzorroUKR/openprocurement.documentservice/ for uploading documents to S3 storage


Install package
```
pip install git+https://git.prozorro.gov.ua/cdb/openprocurement.storage.s3.git
```
    
Install package for development with documentservice
```
git clone git@git.prozorro.gov.ua:cdb/openprocurement.documentservice.git
cd openprocurement.documentservice
pip install -r requirements.txt
pip install -e .[test,docs]
git clone git@git.prozorro.gov.ua:cdb/openprocurement.storage.s3.git ./src/openprocurement.storage.s3
pip install -e src/openprocurement.storage.s3[test]
```

Add next settings to service.ini:
```
[app:docservice]
storage = s3
s3.access_key = access_key
s3.bucket = bucket
s3.region = region
s3.secret_key = secret_key
```

Backend for https://github.com/ProzorroUKR/openprocurement.documentservice/ for uploading documents to S3 storage

Requires Python 3.13 and [uv](https://docs.astral.sh/uv/).

Install:

    uv sync

`documentservice` is pulled from git over SSH, so you need access to
`git.prozorro.gov.ua`.

Run the tests:

    uv run pytest

Add next settings to service.ini:
```
[app:docservice]
storage = s3
s3.access_key = access_key
s3.bucket = bucket
s3.region = region
s3.secret_key = secret_key
```

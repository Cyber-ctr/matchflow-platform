from abc import ABC, abstractmethod
from io import BytesIO
from pathlib import Path
from shutil import copyfileobj
from uuid import uuid4

from botocore.exceptions import ClientError
from flask import current_app


class ObjectStorage(ABC):
    @abstractmethod
    def save(self, stream, category, user_id, extension, content_type):
        raise NotImplementedError

    @abstractmethod
    def open(self, key):
        raise NotImplementedError


class LocalObjectStorage(ObjectStorage):
    def __init__(self, root):
        self.root = Path(root).resolve()

    def save(self, stream, category, user_id, extension, content_type):
        key = f'{category}/{user_id}/{uuid4().hex}{extension}'
        target = (self.root / key).resolve()
        if self.root not in target.parents:
            raise ValueError('Invalid storage key.')
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('wb') as destination:
            copyfileobj(stream, destination)
        return key

    def open(self, key):
        target = (self.root / key).resolve()
        if self.root not in target.parents:
            raise ValueError('Invalid storage key.')
        return BytesIO(target.read_bytes())


class S3ObjectStorage(ObjectStorage):
    def __init__(self, bucket, endpoint_url, region, prefix):
        import boto3

        self.bucket = bucket
        self.prefix = prefix.strip('/')
        self.client = boto3.client(
            's3',
            endpoint_url=endpoint_url or None,
            region_name=region,
        )

    def save(self, stream, category, user_id, extension, content_type):
        key = f'{category}/{user_id}/{uuid4().hex}{extension}'
        object_key = f'{self.prefix}/{key}' if self.prefix else key
        self.client.upload_fileobj(
            stream,
            self.bucket,
            object_key,
            ExtraArgs={'ContentType': content_type or 'application/octet-stream'},
        )
        return key

    def open(self, key):
        object_key = f'{self.prefix}/{key}' if self.prefix else key
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=object_key)
        except ClientError as error:
            if error.response.get('Error', {}).get('Code') in {'NoSuchKey', '404', 'NotFound'}:
                raise FileNotFoundError(key) from error
            raise
        return BytesIO(response['Body'].read())

def get_storage():
    bucket = current_app.config.get('OBJECT_STORAGE_BUCKET')
    if bucket:
        return S3ObjectStorage(
            bucket=bucket,
            endpoint_url=current_app.config.get('OBJECT_STORAGE_ENDPOINT_URL'),
            region=current_app.config.get('OBJECT_STORAGE_REGION', 'auto'),
            prefix=current_app.config.get('OBJECT_STORAGE_PREFIX', 'matchflow'),
        )
    return LocalObjectStorage(current_app.config['UPLOAD_FOLDER'])

from collections.abc import Generator
from typing import Union

from flask import Flask

from config import app_config
from services.storge.aliyun_storage import AliyunStorage
from services.storge.local_storage import LocalStorage
from services.storge.s3_storage import S3Storage


class Storage:
    def __init__(self):
        self.storage_runner = None

    def init_app(self, app: Flask):
        storage_type = app.config.get('STORAGE_TYPE')
        if storage_type == 's3':
            self.storage_runner = S3Storage(
                app=app
            )
        elif storage_type == 'aliyun-oss':
            self.storage_runner = AliyunStorage(
                app=app
            )
        else:
            self.storage_runner = LocalStorage(app=app)

    def save(self, filename, data):
        self.storage_runner.save(filename, data)

    def load(self, filename: str, stream: bool = False) -> Union[bytes, Generator]:
        if stream:
            return self.load_stream(filename)
        else:
            return self.load_once(filename)

    def load_once(self, filename: str) -> bytes:
        return self.storage_runner.load_once(filename)

    def load_stream(self, filename: str) -> Generator:
        return self.storage_runner.load_stream(filename)

    def download(self, filename, target_filepath):
        self.storage_runner.download(filename, target_filepath)

    def exists(self, filename):
        return self.storage_runner.exists(filename)

    def delete(self, filename):
        return self.storage_runner.delete(filename)


storage = Storage()


def init_app(app: Flask):
    storage.init_app(app)

import datetime
import hashlib
import uuid

from werkzeug.datastructures import FileStorage
from collections.abc import Generator

from werkzeug.exceptions import NotFound

from config import app_config
from services.database.postgres_db import db
from services.db_model.uploadfile import UploadFile
from services.storge import storage
from services.utils.upload_file_parser import UploadFileParser
from utils.error.file_error import UnsupportedFileTypeError, FileTooLargeError

IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'webp', 'gif', 'svg']
IMAGE_EXTENSIONS.extend([ext.upper() for ext in IMAGE_EXTENSIONS])

PREVIEW_WORDS_LIMIT = 3000


class FileService:

    @staticmethod
    def upload_file(file: FileStorage,only_image: bool = False) -> UploadFile:
        filename = file.filename
        extension = file.filename.split('.')[-1]
        if len(filename) > 200:
            filename = filename.split('.')[0][:200] + '.' + extension
        allowed_extensions =  IMAGE_EXTENSIONS
        if extension.lower() not in allowed_extensions:
            raise UnsupportedFileTypeError("file format no support")
        elif only_image and extension.lower() not in IMAGE_EXTENSIONS:
            raise UnsupportedFileTypeError()

        # read file content
        file_content = file.read()

        # get file size
        file_size = len(file_content)

        if extension.lower() in IMAGE_EXTENSIONS:
            file_size_limit = app_config.UPLOAD_IMAGE_FILE_SIZE_LIMIT * 1024 * 1024
        else:
            file_size_limit = app_config.UPLOAD_FILE_SIZE_LIMIT * 1024 * 1024

        if file_size > file_size_limit:
            message = f'File size exceeded. {file_size} > {file_size_limit}'
            raise FileTooLargeError(message)

        user_uuid = str(uuid.uuid4())
        tenant_id = user_uuid
        # user uuid as file name
        file_uuid = str(uuid.uuid4())


        file_key = 'upload_files/' + user_uuid + '/' + file_uuid + '.' + extension

        # save file to storage
        storage.save(file_key, file_content)

        # save file to db
        upload_file = UploadFile(
            tenant_id=tenant_id,
            storage_type=app_config.STORAGE_TYPE,
            key=file_key,
            name=filename,
            size=file_size,
            extension=extension,
            mime_type=file.mimetype,
            created_by_role='account',
            created_by=user_uuid,
            created_at=datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None),
            used=False,
            hash=hashlib.sha3_256(file_content).hexdigest()
        )

        db.session.add(upload_file)
        db.session.commit()

        return upload_file

    @staticmethod
    def get_public_image_preview(file_id: str) -> tuple[Generator, str]:
        upload_file = db.session.query(UploadFile) \
            .filter(UploadFile.id == file_id) \
            .first()

        if not upload_file:
            raise NotFound("File not found or signature is invalid")

        # extract text from file
        extension = upload_file.extension
        if extension.lower() not in IMAGE_EXTENSIONS:
            raise UnsupportedFileTypeError()

        imagebase64 = UploadFileParser.get_image_data(upload_file)

        return imagebase64, upload_file.mime_type
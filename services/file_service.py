import datetime
import hashlib
import uuid

from werkzeug.datastructures import FileStorage

from config import app_config
from services.db_model.uploadfile import UploadFile
from utils.error.file_error import UnsupportedFileTypeError, FileTooLargeError

IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'webp', 'gif', 'svg']
IMAGE_EXTENSIONS.extend([ext.upper() for ext in IMAGE_EXTENSIONS])

ALLOWED_EXTENSIONS = ['txt', 'markdown', 'md', 'pdf', 'html', 'htm', 'xlsx', 'xls', 'docx', 'csv']
UNSTRUCTURED_ALLOWED_EXTENSIONS = ['txt', 'markdown', 'md', 'pdf', 'html', 'htm', 'xlsx', 'xls',
                                   'docx', 'csv', 'eml', 'msg', 'pptx', 'ppt', 'xml', 'epub']

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
            raise UnsupportedFileTypeError()
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

        user_uuid = "2312452441234"
        convesation_id = "231212312312"

        # user uuid as file name
        file_uuid = str(uuid.uuid4())

        file_key = 'upload_files/' + user_uuid + '/' + file_uuid + '.' + extension

        # save file to storage
        # storage.save(file_key, file_content)

        # save file to db
        upload_file = UploadFile(
            user_uuid=user_uuid,
            convesation_id=convesation_id,
            storage_type=app_config.STORAGE_TYPE,
            key=file_key,
            name=filename,
            name_id = file_uuid,
            size=file_size,
            extension=extension,
            mime_type=file.mimetype,
            created_by=user_uuid,
            created_at= str(datetime.datetime.now()),
            hash=hashlib.sha3_256(file_content).hexdigest()
        )

        return upload_file
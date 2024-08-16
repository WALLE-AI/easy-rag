
from flask import request
from flask_restful import Resource, marshal_with

from config import app_config
from controllers.entities.file_entity import file_fields, upload_config_fields
from controllers.file import api
from services.file_service import FileService
from utils.error.error import NoFileUploadedError, TooManyFilesError, UnsupportedFileTypeError
from utils.error.file_error import FileTooLargeError


class FileApi(Resource):

    @marshal_with(upload_config_fields)
    def get(self):
        ##文件和图片大小需要设置限制大小
        file_size_limit = app_config.UPLOAD_FILE_SIZE_LIMIT
        batch_count_limit = app_config.UPLOAD_FILE_BATCH_LIMIT
        image_file_size_limit = app_config.UPLOAD_IMAGE_FILE_SIZE_LIMIT
        return {
            'file_size_limit': file_size_limit,
            'batch_count_limit': batch_count_limit,
            'image_file_size_limit': image_file_size_limit
        }, 200
    @marshal_with(file_fields)
    def post(self):

        # get file from request
        file = request.files['file']

        # check file
        if 'file' not in request.files:
            raise NoFileUploadedError()

        if len(request.files) > 1:
            raise TooManyFilesError()
        try:
            upload_file = FileService.upload_file(file)
        except FileTooLargeError as file_too_large_error:
            raise FileTooLargeError(file_too_large_error.description)
        except UnsupportedFileTypeError:
            raise UnsupportedFileTypeError()

        return upload_file, 201

api.add_resource(FileApi, '/files/upload')
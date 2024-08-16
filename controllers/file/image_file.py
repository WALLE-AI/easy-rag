from flask import request, Response
from flask_restful import Resource

from controllers.entities.file_entity import ImageFilePreview
from controllers.file import api
from services.file_service import FileService
from utils.error.error import UnsupportedFileTypeError


class ImagePreviewApi(Resource):
    def get(self):
        file_id =request.args.get('file_id')
        try:
            imagebase64, mimetype = FileService.get_public_image_preview(
                file_id
            )
        except UnsupportedFileTypeError:
            raise UnsupportedFileTypeError()

        image_file_preview = ImageFilePreview(
            mime_type=mimetype,
            imagebase64=imagebase64
        )
        return image_file_preview.to_dict(),201


api.add_resource(ImagePreviewApi, '/files/image-preview')
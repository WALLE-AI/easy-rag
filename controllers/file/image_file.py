from flask import request, Response
from flask_restful import Resource

from controllers.file import api
from services.file_service import FileService
from utils.error.error import UnsupportedFileTypeError


class ImagePreviewApi(Resource):
    def get(self):
        file_id =request.args.get('file_id')
        try:
            generator, mimetype = FileService.get_public_image_preview(
                file_id
            )
        except UnsupportedFileTypeError:
            raise UnsupportedFileTypeError()

        return Response(generator, mimetype=mimetype)


api.add_resource(ImagePreviewApi, '/files/image-preview')
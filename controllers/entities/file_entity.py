from pydantic import BaseModel
from flask_restful import fields
from model_runtime.utils.encoders import jsonable_encoder



upload_config_fields = {
    'file_size_limit': fields.Integer,
    'batch_count_limit': fields.Integer,
    'image_file_size_limit': fields.Integer,
}

file_fields = {
    'id': fields.String,
    'name': fields.String,
    'size': fields.Integer,
    'extension': fields.String,
    'mime_type': fields.String,
    'created_by': fields.String,
    'created_at': fields.String,
}


class ImageFilePreview(BaseModel):
    mime_type:str="image/png"
    imagebase64:str=""
    def to_dict(self) -> dict:
        return jsonable_encoder(self)

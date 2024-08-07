from flask_restful import fields
class TimestampField(fields.Raw):
    def format(self, value) -> int:
        return int(value.timestamp())



upload_config_fields = {
    'file_size_limit': fields.Integer,
    'batch_count_limit': fields.Integer,
    'image_file_size_limit': fields.Integer,
}

file_fields = {
    'user_uuid': fields.String,
    'name': fields.String,
    "name_id":fields.String,
    'size': fields.Integer,
    'extension': fields.String,
    'mime_type': fields.String,
    'created_by': fields.String,
    'created_at': fields.String,
}
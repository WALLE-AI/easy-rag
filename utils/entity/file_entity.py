from flask_restful import fields
class TimestampField(fields.Raw):
    def format(self, value) -> int:
        return int(value.timestamp())
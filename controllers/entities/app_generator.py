from pydantic import BaseModel

from model_runtime.utils.encoders import jsonable_encoder


class AppGeneratorMessage(BaseModel):
    event:str="message"
    conversation_id:str="9c059a09-a3b2-4ac6-a980-fff88959511c"
    message_id:str="d11e452b-c256-43fc-9a5a-f60f2854cb52"
    created_at:int=1723688098
    usage:dict=None
    answer:str="d11e452b-c256-43fc-9a5a-f60f2854cb52"
    def to_dict(self) -> dict:
        return jsonable_encoder(self)

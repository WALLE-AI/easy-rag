from pydantic import BaseModel


class UploadFile(BaseModel):
    '''
    user_uuid: str 用户ID
    convesation_id: str 当前对话ID
    storage_type:str= 对象存储方式
    key:str 文件存储目录 比如oss服务buck_name
    name:str 文件名称
    name_id 文件ID
    size:int 文件大小
    extension:str 文件格式
    mime_type:str 文件格式
    created_at:str 创建时间
    created_by:str 创建账号的ID，这里取user_uuid
    hash:str 内容hash值
    '''
    user_uuid: str
    convesation_id:str
    storage_type:str="aliyun_oss"
    key:str
    name:str
    name_id:str
    size:int
    extension:str
    mime_type:str
    created_by:str
    created_at:str
    hash:str
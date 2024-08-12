from services.database.postgres_db import db
from services.db_model import StringUUID


class UploadFile(db.Model):
    __tablename__ = 'upload_files'
    __table_args__ = (
        db.PrimaryKeyConstraint('id', name='upload_file_pkey'),
        db.Index('upload_file_tenant_idx', 'tenant_id')
    )

    id = db.Column(StringUUID, server_default=db.text('uuid_generate_v4()'))
    tenant_id = db.Column(StringUUID, nullable=False)
    storage_type = db.Column(db.String(255), nullable=False)
    key = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    size = db.Column(db.Integer, nullable=False)
    extension = db.Column(db.String(255), nullable=False)
    mime_type = db.Column(db.String(255), nullable=True)
    created_by_role = db.Column(db.String(255), nullable=False, server_default=db.text("'account'::character varying"))
    created_by = db.Column(StringUUID, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.text('CURRENT_TIMESTAMP(0)'))
    used = db.Column(db.Boolean, nullable=False, server_default=db.text('false'))
    used_by = db.Column(StringUUID, nullable=True)
    used_at = db.Column(db.DateTime, nullable=True)
    hash = db.Column(db.String(255), nullable=True)



# class UploadFile(BaseModel):
#     '''
#     user_uuid: str 用户ID
#     convesation_id: str 当前对话ID
#     storage_type:str= 对象存储方式
#     key:str 文件存储目录 比如oss服务buck_name
#     name:str 文件名称
#     name_id 文件ID
#     size:int 文件大小
#     extension:str 文件格式
#     mime_type:str 文件格式
#     created_at:str 创建时间
#     created_by:str 创建账号的ID，这里取user_uuid
#     hash:str 内容hash值
#     '''
#     user_uuid: str
#     convesation_id:str
#     storage_type:str="aliyun_oss"
#     key:str
#     name:str
#     name_id:str
#     size:int
#     extension:str
#     mime_type:str
#     created_by:str
#     created_at:str
#     hash:str
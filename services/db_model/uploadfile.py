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

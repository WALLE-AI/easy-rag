from services.database.postgres_db import db


from services.db_model import StringUUID
class Message(db.Model):
    __tablename__ = 'messages'
    __table_args__ = (
        db.PrimaryKeyConstraint('id', name='message_pkey'),
        db.Index('message_conversation_id_idx', 'conversation_id'),
        db.Index('message_account_idx',  'from_account_id'),
    )

    id = db.Column(StringUUID, server_default=db.text('uuid_generate_v4()'))
    model_provider = db.Column(db.String(255), nullable=True)
    file_id = db.Column(StringUUID, nullable=False)
    model_id = db.Column(db.String(255), nullable=True)
    conversation_id = db.Column(StringUUID, nullable=False)
    query = db.Column(db.Text, nullable=False)
    message = db.Column(db.JSON, nullable=False)
    message_tokens = db.Column(db.Integer, nullable=False, server_default=db.text('0'))
    message_unit_price = db.Column(db.Numeric(10, 4), nullable=False)
    message_price_unit = db.Column(db.Numeric(10, 7), nullable=False, server_default=db.text('0.001'))
    answer = db.Column(db.Text, nullable=False)
    answer_tokens = db.Column(db.Integer, nullable=False, server_default=db.text('0'))
    answer_unit_price = db.Column(db.Numeric(10, 4), nullable=False)
    answer_price_unit = db.Column(db.Numeric(10, 7), nullable=False, server_default=db.text('0.001'))
    provider_response_latency = db.Column(db.Float, nullable=False, server_default=db.text('0'))
    total_price = db.Column(db.Numeric(10, 7))
    currency = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(255), nullable=False, server_default=db.text("'normal'::character varying"))
    error = db.Column(db.Text)
    message_metadata = db.Column(db.Text)
    from_account_id = db.Column(StringUUID)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.text('CURRENT_TIMESTAMP(0)'))
    updated_at = db.Column(db.DateTime, nullable=False, server_default=db.text('CURRENT_TIMESTAMP(0)'))

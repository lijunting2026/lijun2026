from sqlalchemy import Column, String, Text, ForeignKey, Boolean
from sqlalchemy.types import Uuid
from app.models.base import BaseModel

class ChatMessage(BaseModel):
    __tablename__ = "chat_messages"
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    session_id = Column(String(50), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    context_type = Column(String(20), nullable=True)
    context_id = Column(String(50), nullable=True)
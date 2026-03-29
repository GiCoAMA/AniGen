from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func

from app.db.database import Base


class ImageTask(Base):
    __tablename__ = "image_tasks"

    # Stored as string for SQLite compatibility; API still treats it as UUID.
    id = Column(String(36), primary_key=True)
    prompt = Column(String, nullable=False)
    status = Column(String, nullable=False, default="PENDING", server_default="PENDING")
    image_url = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

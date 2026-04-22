from sqlalchemy import Column, Integer, String, Boolean
from code.backend.models.database import Base

class TodoModel(Base):
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String, nullable=False)
    completed = Column(Boolean, default=False)
    category = Column(String, default="General")
    priority = Column(String, default="Medium")




"""
Модель команды (таблица в БД)
Ничего менять не нужно
"""

from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.database import Base

class Team(Base):
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True, index=True)
    team_name = Column(String(200), nullable=False)
    captain_name = Column(String(100), nullable=False)
    captain_email = Column(String(100), nullable=False)
    participant_count = Column(Integer, nullable=False)
    institution = Column(String(200), nullable=True)
    qr_code_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
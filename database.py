from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from datetime import datetime


class Base(DeclarativeBase):
    pass


class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True)
    text = Column(String, nullable=False)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    deadline = Column(String, nullable=True)  # Будем хранить как строку 'YYYY-MM-DD'

    def to_dict(self):
        """Преобразует объект задачи в словарь"""
        return {
            'id': self.id,
            'text': self.text,
            'completed': self.completed,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None,
            'deadline': self.deadline
        }


engine = create_engine('sqlite:///study_planner.db', echo=False)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def get_session():
    return Session()

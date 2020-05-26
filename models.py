from sqlalchemy import (
    Column, 
    Integer,
    String,
)
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Video(Base):
    __tablename__ = 'video'
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False, unique=False)
    duration = Column(Integer, nullable=False, unique=False)
    views = Column(Integer, nullable=False, unique=False)
    channel = Column(String, nullable=False, unique=False)
    # playlist = Column(String, nullable=True, unique=False)
    # description = Column(String, nullable=True, unique=False)
#     comments

class Channel(Base):
    __tablename__ = 'channel'
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False, unique=False)
    duration = Column(String, nullable=False, unique=False)
    views = Column(Integer, nullable=False, unique=False)
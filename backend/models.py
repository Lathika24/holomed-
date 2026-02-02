"""
Database models for HoloMed
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    subscription_tier = Column(String, default="free")  # free, pro, enterprise
    created_at = Column(DateTime, default=datetime.utcnow)
    
    models = relationship("Model3D", back_populates="owner", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")

class Model3D(Base):
    __tablename__ = "models"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)  # Local path or S3/GCS path
    file_format = Column(String, nullable=False)  # stl, obj, ply, vtk, gltf, glb
    file_size = Column(Integer)  # Size in bytes
    created_at = Column(DateTime, default=datetime.utcnow)
    
    owner = relationship("User", back_populates="models")
    sessions = relationship("Session", back_populates="model", cascade="all, delete-orphan")

class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    model_id = Column(Integer, ForeignKey("models.id"), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    gesture_data = Column(JSON, nullable=True)  # Store gesture analytics
    
    user = relationship("User", back_populates="sessions")
    model = relationship("Model3D", back_populates="sessions")

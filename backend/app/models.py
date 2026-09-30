"""Database models (SQLite via SQLAlchemy)."""
import os
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

load_dotenv()
DB_URL = os.getenv("DATABASE_URL", "sqlite:///./janvikas.db")
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False)
Base = declarative_base()


class District(Base):  # SYNTHETIC sample demographics
    __tablename__ = "districts"
    name = Column(String, primary_key=True)
    lat = Column(Float); lng = Column(Float)
    population = Column(Integer)
    vulnerability = Column(Float)  # 0-100 synthetic index


class Infrastructure(Base):  # SYNTHETIC gap score per district+category (0-100, higher = worse)
    __tablename__ = "infrastructure"
    id = Column(Integer, primary_key=True)
    district = Column(String, index=True); category = Column(String)
    gap_score = Column(Float)


class Investment(Base):  # SYNTHETIC per-capita investment (INR)
    __tablename__ = "investments"
    id = Column(Integer, primary_key=True)
    district = Column(String, index=True); category = Column(String)
    per_capita_inr = Column(Float)


class CitizenRequest(Base):
    __tablename__ = "requests"
    id = Column(Integer, primary_key=True)
    request_id = Column(String, unique=True, index=True)
    text = Column(Text); district = Column(String, index=True)
    location = Column(String, nullable=True)
    category_hint = Column(String, nullable=True)
    input_mode = Column(String, default="text")
    is_synthetic = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    analysis = relationship("Analysis", uselist=False, back_populates="request", cascade="all, delete-orphan")


class Analysis(Base):
    __tablename__ = "analyses"
    id = Column(Integer, primary_key=True)
    request_pk = Column(Integer, ForeignKey("requests.id"), unique=True)
    language = Column(String); category = Column(String, index=True)
    problem = Column(Text); location = Column(String, nullable=True)
    severity = Column(String); explanation = Column(Text)
    source = Column(String)  # "gemini" or "keyword-fallback"
    request = relationship("CitizenRequest", back_populates="analysis")


class Recommendation(Base):
    __tablename__ = "recommendations"
    id = Column(Integer, primary_key=True)
    district = Column(String); category = Column(String)
    title = Column(String); action = Column(Text)
    request_count = Column(Integer); score = Column(Float)
    affected_population = Column(Integer)
    factors = Column(Text)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

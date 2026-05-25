from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    monitors = relationship("Monitor", back_populates="owner")

class Monitor(Base):
    __tablename__ = "monitors"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    interval_seconds = Column(Integer, default=60)
    expected_status = Column(Integer, default=200)
    expected_body_contains = Column(String, nullable=True)
    timeout_ms = Column(Integer, default=5000)
    is_active = Column(Boolean, default=True)
    last_checked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="monitors")
    results = relationship("CheckResult", back_populates="monitor")
    alerts = relationship("Alert", back_populates="monitor")

class CheckResult(Base):
    __tablename__ = "check_results"

    id = Column(Integer, primary_key=True, index=True)
    monitor_id = Column(Integer, ForeignKey("monitors.id"))
    checked_at = Column(DateTime(timezone=True), server_default=func.now())
    status_code = Column(Integer, nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    passed = Column(Boolean, nullable=False)
    error_message = Column(String, nullable=True)

    monitor = relationship("Monitor", back_populates="results")

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    monitor_id = Column(Integer, ForeignKey("monitors.id"))
    triggered_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    consecutive_failures = Column(Integer, default=0)
    webhook_url = Column(String, nullable=False)

    monitor = relationship("Monitor", back_populates="alerts")

"""Database models for April Shipments Bot."""

from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, String, DECIMAL, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    """User model for storing Telegram user information."""

    __tablename__ = 'users'

    user_id = Column(BigInteger, primary_key=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    registration_date = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    last_activity = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    bookings = relationship("Booking", back_populates="user")

    def __repr__(self):
        return f"<User(user_id={self.user_id}, username={self.username})>"


class Shipment(Base):
    """Shipment model for storing shipment information."""

    __tablename__ = 'shipments'

    shipment_id = Column(String(50), primary_key=True)
    loading_point = Column(String(255), nullable=False)
    loading_date = Column(DateTime, nullable=False)
    direction = Column(String(255), nullable=False)
    weight = Column(DECIMAL(10, 2), nullable=False)
    volume = Column(DECIMAL(10, 2), nullable=False)
    start_address = Column(Text, nullable=False)
    end_address = Column(Text, nullable=False)
    points_count = Column(Integer, nullable=False)
    distance = Column(Integer, nullable=False)
    cost = Column(String(100), nullable=False)
    vehicle = Column(String(255), nullable=False)
    driver = Column(String(255), nullable=False)
    status = Column(String(20), default='available')  # available / booked
    booked_by = Column(String(255), nullable=True)  # username, not user_id
    booked_at = Column(DateTime, nullable=True)
    publication_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    synced_from_sheet = Column(Boolean, default=False)

    # Relationships
    bookings = relationship("Booking", back_populates="shipment")

    def __repr__(self):
        return f"<Shipment(shipment_id={self.shipment_id}, direction={self.direction}, status={self.status})>"


class Booking(Base):
    """Booking history model for tracking all booking actions."""

    __tablename__ = 'bookings'

    booking_id = Column(Integer, primary_key=True, autoincrement=True)
    shipment_id = Column(String(50), ForeignKey('shipments.shipment_id'), nullable=False)
    user_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    username = Column(String(255), nullable=False)
    action = Column(String(20), nullable=False)  # 'booked' / 'cancelled'
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    shipment = relationship("Shipment", back_populates="bookings")
    user = relationship("User", back_populates="bookings")

    def __repr__(self):
        return f"<Booking(booking_id={self.booking_id}, shipment_id={self.shipment_id}, action={self.action})>"

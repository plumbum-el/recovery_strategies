from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(100), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=True)

    recovery_strategies = relationship(
        "RecoveryStrategy",
        back_populates="creator"
    )

    likes = relationship(
        "RecoveryStrategyLike",
        back_populates="user"
    )


class RecoveryStrategy(Base):
    __tablename__ = "recovery_strategies"

    id = Column(Integer, primary_key=True)

    title = Column(String(150), nullable=False)
    short_description = Column(String(500))

    status = Column(String(20), nullable=False)

    image_url = Column(String(500))
    video_url = Column(String(500))

    estimated_time = Column(Integer)
    cost = Column(Integer)

    created_at = Column(DateTime, nullable=False)
    published_at = Column(DateTime)

    creator_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    creator = relationship(
        "User",
        back_populates="recovery_strategies"
    )

    likes = relationship(
        "RecoveryStrategyLike",
        back_populates="recovery_strategy"
    )


class RecoveryStrategyLike(Base):
    __tablename__ = "recovery_strategy_likes"

    id = Column(Integer, primary_key=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    recovery_strategy_id = Column(
        Integer,
        ForeignKey("recovery_strategies.id"),
        nullable=False
    )

    user = relationship(
        "User",
        back_populates="likes"
    )

    recovery_strategy = relationship(
        "RecoveryStrategy",
        back_populates="likes"
    )

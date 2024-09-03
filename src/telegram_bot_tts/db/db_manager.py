import uuid
from datetime import datetime, date
from sqlalchemy import (
    create_engine,
    Column,
    String,
    Integer,
    DateTime,
    Date,
    Enum,
    ForeignKey,
    Boolean,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_premier = Column(Boolean, default=False, nullable=False)

    behaviors = relationship("UserBehavior", back_populates="user")
    limits = relationship("UserLimit", back_populates="user")


class UserBehavior(Base):
    __tablename__ = "user_behaviors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    function_type = Column(Enum("text_to_audio", "audio_to_text", name="function_type"))
    tokens_used = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="behaviors")


class UserLimit(Base):
    __tablename__ = "user_limits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    total_tokens_limit = Column(Integer, nullable=False)
    tokens_used = Column(Integer, default=0)
    reset_date = Column(Date, nullable=False)

    user = relationship("User", back_populates="limits")


class DBManager:
    def __init__(self, db_url):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def create_user(self, username, email, is_premier=False):
        session = self.Session()
        new_user = User(username=username, email=email, is_premier=is_premier)
        session.add(new_user)
        session.commit()
        user_id = new_user.id
        session.close()
        return user_id

    def get_user(self, user_id):
        session = self.Session()
        user = session.query(User).filter(User.id == user_id).first()
        session.close()
        return user

    def update_user_premier_status(self, user_id, is_premier):
        session = self.Session()
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            user.is_premier = is_premier
            user.updated_at = datetime.utcnow()
            session.commit()
        session.close()

    def record_behavior(self, user_id, function_type, tokens_used):
        session = self.Session()
        new_behavior = UserBehavior(
            user_id=user_id, function_type=function_type, tokens_used=tokens_used
        )
        session.add(new_behavior)
        session.commit()
        session.close()

    def get_user_behaviors(self, user_id):
        session = self.Session()
        behaviors = (
            session.query(UserBehavior).filter(UserBehavior.user_id == user_id).all()
        )
        session.close()
        return behaviors

    def set_user_limit(self, user_id, total_tokens_limit, reset_date):
        session = self.Session()
        new_limit = UserLimit(
            user_id=user_id,
            total_tokens_limit=total_tokens_limit,
            reset_date=reset_date,
        )
        session.add(new_limit)
        session.commit()
        session.close()

    def update_user_tokens(self, user_id, tokens_used):
        session = self.Session()
        user_limit = (
            session.query(UserLimit).filter(UserLimit.user_id == user_id).first()
        )
        if user_limit:
            user_limit.tokens_used += tokens_used
            session.commit()
        session.close()

    def check_user_limit(self, user_id):
        session = self.Session()
        user_limit = (
            session.query(UserLimit).filter(UserLimit.user_id == user_id).first()
        )
        if user_limit:
            remaining_tokens = user_limit.total_tokens_limit - user_limit.tokens_used
            is_within_limit = remaining_tokens > 0
        else:
            remaining_tokens = 0
            is_within_limit = False
        session.close()
        return is_within_limit, remaining_tokens


# Usage example
if __name__ == "__main__":
    
    db_url = "postgresql://admin:secure_password@127.0.0.1:5432/user_system"
    
    db_manager = DBManager(db_url)

    # Create a new user
    user_id = db_manager.create_user("johndoe", "john@example.com", is_premier=False)

    # Set user limit
    db_manager.set_user_limit(user_id, 1000, date.today())

    # Record user behavior
    db_manager.record_behavior(user_id, "text_to_audio", 50)

    # Check user limit
    is_within_limit, remaining_tokens = db_manager.check_user_limit(user_id)
    print(f"User within limit: {is_within_limit}, Remaining tokens: {remaining_tokens}")

    # Get user behaviors
    behaviors = db_manager.get_user_behaviors(user_id)
    for behavior in behaviors:
        print(
            f"Function: {behavior.function_type}, Tokens used: {behavior.tokens_used}"
        )

    # Update user's premier status
    db_manager.update_user_premier_status(user_id, True)

    # Get updated user info
    updated_user = db_manager.get_user(user_id)
    print(f"User {updated_user.username} is premier: {updated_user.is_premier}")

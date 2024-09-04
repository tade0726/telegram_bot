'''
Todo:
    - add logging
'''


from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from sqlalchemy import text

from datetime import datetime, timedelta
import os


Base = declarative_base()



class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Subscription(Base):
    __tablename__ = "subscriptions"
    subscription_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    plan_name = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    tts_monthly_limit = Column(Integer)
    stt_monthly_limit = Column(Integer)


class Payment(Base):
    __tablename__ = "payments"
    payment_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    subscription_id = Column(Integer, ForeignKey("subscriptions.subscription_id"))
    amount = Column(Float, nullable=False)
    payment_date = Column(DateTime(timezone=True), server_default=func.now())
    payment_method = Column(String(50))


class TTSActivity(Base):
    __tablename__ = "tts_activity"
    tts_activity_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    character_count = Column(Integer, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())


class STTActivity(Base):
    __tablename__ = "stt_activity"
    stt_activity_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    duration_seconds = Column(Integer, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())


class DBManager:
    def __init__(self, db_url=None):
        if db_url is None:
            db_username = os.getenv("DB_USERNAME")
            db_password = os.getenv("DB_PASSWORD")
            db_host = os.getenv("DB_HOST")
            db_port = os.getenv("DB_PORT")
            db_name = os.getenv("DB_NAME")

            if any(
                var is None
                for var in [db_username, db_password, db_host, db_port, db_name]
            ):
                raise ValueError(
                    "One or more required database environment variables are missing."
                )

            db_url = f"postgresql://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}"

        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def add_user(self, user_id, username, email, password_hash):
        session = self.Session()
        try:
            # Check if user_id, username, or email already exist
            existing_user = (
                session.query(User)
                .filter(
                    (User.user_id == user_id)
                    | (User.username == username)
                    | (User.email == email)
                )
                .first()
            )

            if existing_user:
                session.close()
                return None  # User already exists

            # If no existing user found, create a new one
            new_user = User(
                user_id=user_id,
                username=username,
                email=email,
                password_hash=password_hash,
            )
            session.add(new_user)
            session.commit()
            user_id = new_user.user_id
            return user_id
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def add_subscription(
        self, user_id, plan_name, start_date, end_date, tts_limit, stt_limit
    ):
        session = self.Session()
        new_subscription = Subscription(
            user_id=user_id,
            plan_name=plan_name,
            start_date=start_date,
            end_date=end_date,
            tts_monthly_limit=tts_limit,
            stt_monthly_limit=stt_limit,
        )
        session.add(new_subscription)
        session.commit()
        subscription_id = new_subscription.subscription_id
        session.close()
        return subscription_id

    def add_payment(self, user_id, subscription_id, amount, payment_method):
        session = self.Session()
        new_payment = Payment(
            user_id=user_id,
            subscription_id=subscription_id,
            amount=amount,
            payment_method=payment_method,
        )
        session.add(new_payment)
        session.commit()
        payment_id = new_payment.payment_id
        session.close()
        return payment_id

    def add_tts_activity(self, user_id, character_count):
        session = self.Session()
        new_activity = TTSActivity(user_id=user_id, character_count=character_count)
        session.add(new_activity)
        session.commit()
        activity_id = new_activity.tts_activity_id
        session.close()
        return activity_id

    def add_stt_activity(self, user_id, duration_seconds):
        session = self.Session()
        new_activity = STTActivity(user_id=user_id, duration_seconds=duration_seconds)
        session.add(new_activity)
        session.commit()
        activity_id = new_activity.stt_activity_id
        session.close()
        return activity_id

    def create_stt_usage_view(self):
        session = self.Session()
        try:
            session.execute(
                text(
                    """
                CREATE OR REPLACE VIEW stt_usage AS
                SELECT u.user_id,
                       u.username,
                       s.plan_name,
                       s.stt_monthly_limit,
                       COALESCE(SUM(sa.duration_seconds), 0::bigint) AS total_stt_usage,
                       s.stt_monthly_limit - COALESCE(SUM(sa.duration_seconds), 0::bigint) AS remaining_stt_limit
                FROM users u
                LEFT JOIN subscriptions s ON u.user_id = s.user_id AND s.is_active = true
                LEFT JOIN stt_activity sa ON u.user_id = sa.user_id AND sa.timestamp >= 
                    date_trunc('month'::text, CURRENT_DATE::timestamp with time zone)
                GROUP BY u.user_id, u.username, s.plan_name, s.stt_monthly_limit
            """
                )
            )
            session.commit()
            print("STT usage view created successfully.")
        except Exception as e:
            session.rollback()
            print(f"Error creating STT usage view: {str(e)}")
        finally:
            session.close()

    def create_tts_usage_view(self):
        session = self.Session()
        try:
            session.execute(
                text(
                    """
                CREATE OR REPLACE VIEW tts_usage AS
                SELECT u.user_id,
                       u.username,
                       s.plan_name,     
                       s.tts_monthly_limit,
                       COALESCE(SUM(ta.character_count), 0::bigint) AS total_tts_usage,
                       s.tts_monthly_limit - COALESCE(SUM(ta.character_count), 0::bigint) AS remaining_tts_limit
                FROM users u
                LEFT JOIN subscriptions s ON u.user_id = s.user_id AND s.is_active = true
                LEFT JOIN tts_activity ta ON u.user_id = ta.user_id AND ta.timestamp >= 
                    date_trunc('month'::text, CURRENT_DATE::timestamp with time zone)
                GROUP BY u.user_id, u.username, s.plan_name, s.tts_monthly_limit
            """
                )
            )
            session.commit()
            print("TTS usage view created successfully.")
        except Exception as e:
            session.rollback()
            print(f"Error creating TTS usage view: {str(e)}")
        finally:
            session.close()

    def get_user_stt_usage(self, user_id):
        session = self.Session()
        try:
            result = session.execute(
                text("SELECT * FROM stt_usage WHERE user_id = :user_id"),
                {"user_id": user_id},
            ).fetchone()
            return result
        except Exception as e:
            print(f"Error fetching STT usage: {str(e)}")
            return None
        finally:
            session.close()
            
    def get_user_tts_usage(self, user_id):
        session = self.Session()
        try:
            result = session.execute(
                text("SELECT * FROM tts_usage WHERE user_id = :user_id"),
                {"user_id": user_id},
            ).fetchone()
            return result
        except Exception as e:
            print(f"Error fetching TTS usage: {str(e)}")
            return None
        finally:
            session.close()


if __name__ == "__main__":

    # Create a DBManager instance
    db_manager = DBManager()

    # Create views
    if True:
        db_manager.create_stt_usage_view()
        db_manager.create_tts_usage_view()

    # print user stt usage
    print(db_manager.get_user_stt_usage(3))

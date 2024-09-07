"""
Todo:
    - add logging
"""

import logging
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
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.sql import func
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import ENUM

import os
from datetime import date, timedelta

Base = declarative_base()

logger = logging.getLogger(__name__)


class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    username = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Subscription(Base):
    __tablename__ = "subscriptions"
    subscription_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    tier = Column(
        ENUM("free", "paid", name="subscription_tier"), nullable=False, default="free"
    )
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    tts_monthly_limit_in_chars = Column(Integer)
    stt_monthly_limit_in_seconds = Column(Integer)


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
            db_url = os.environ["DATABASE_URL"]

        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def add_user(self, user_id, username, first_name, last_name):
        session = self.Session()
        try:
            new_user = User(
                user_id=user_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
            )
            session.add(new_user)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error adding user: {str(e)}")
            return False
        finally:
            session.close()

    def add_subscription(
        self,
        user_id,
        tier,
        start_date,
        end_date,
        tts_limit,
        stt_limit,
    ):
        session = self.Session()
        try:
            new_subscription = Subscription(
                user_id=user_id,
                tier=tier,
                start_date=start_date,
                end_date=end_date,
                tts_monthly_limit_in_chars=tts_limit,
                stt_monthly_limit_in_seconds=stt_limit,
            )
            session.add(new_subscription)
            session.commit()
            session.refresh(new_subscription)
            return new_subscription.subscription_id
        except Exception as e:
            session.rollback()
            logger.error(f"Error adding subscription: {str(e)}")
            return False
        finally:
            session.close()

    def add_payment(self, user_id, subscription_id, amount, payment_method):
        session = self.Session()
        try:
            new_payment = Payment(
                user_id=user_id,
                subscription_id=subscription_id,
                amount=amount,
                payment_method=payment_method,
            )
            session.add(new_payment)
            session.commit()
            return new_payment.payment_id
        except Exception as e:
            session.rollback()
            logger.error(f"Error adding payment: {str(e)}")
            return False
        finally:
            session.close()

    def add_tts_activity(self, user_id, character_count):
        session = self.Session()
        try:
            new_activity = TTSActivity(user_id=user_id, character_count=character_count)
            session.add(new_activity)
            session.commit()
            return new_activity.tts_activity_id
        except Exception as e:
            session.rollback()
            logger.error(f"Error adding TTS activity: {str(e)}")
            return False
        finally:
            session.close()

    def add_stt_activity(self, user_id, duration_seconds):
        session = self.Session()
        try:
            new_activity = STTActivity(
                user_id=user_id, duration_seconds=duration_seconds
            )
            session.add(new_activity)
            session.commit()
            return new_activity.stt_activity_id
        except Exception as e:
            session.rollback()
            logger.error(f"Error adding STT activity: {str(e)}")
            return False
        finally:
            session.close()

    def create_stt_usage_view(self):
        session = self.Session()
        try:
            session.execute(
                text(
                    """
                CREATE OR REPLACE VIEW stt_usage AS
                SELECT u.user_id,
                       u.username,
                       s.tier,
                       s.stt_monthly_limit_in_seconds,
                       COALESCE(SUM(sa.duration_seconds), 0) AS total_stt_usage,
                       s.stt_monthly_limit_in_seconds - COALESCE(SUM(sa.duration_seconds), 0) AS remaining_stt_limit
                FROM users u
                LEFT JOIN subscriptions s ON u.user_id = s.user_id
                LEFT JOIN stt_activity sa ON u.user_id = sa.user_id AND sa.timestamp >= 
                    date_trunc('month'::text, CURRENT_DATE::timestamp with time zone)
                GROUP BY u.user_id, u.username, s.tier, s.stt_monthly_limit_in_seconds
            """
                )
            )
            session.commit()
            logger.debug("STT usage view created successfully.")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating STT usage view: {str(e)}")
            return False
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
                       s.tier,     
                       s.tts_monthly_limit_in_chars,
                       COALESCE(SUM(ta.character_count), 0) AS total_tts_usage,
                       s.tts_monthly_limit_in_chars - COALESCE(SUM(ta.character_count), 0) AS remaining_tts_limit
                FROM users u
                LEFT JOIN subscriptions s ON u.user_id = s.user_id
                LEFT JOIN tts_activity ta ON u.user_id = ta.user_id AND ta.timestamp >= 
                    date_trunc('month'::text, CURRENT_DATE::timestamp with time zone)
                GROUP BY u.user_id, u.username, s.tier, s.tts_monthly_limit_in_chars
            """
                )
            )
            session.commit()
            logger.debug("TTS usage view created successfully.")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating TTS usage view: {str(e)}")
            return False
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
            logger.error(f"Error fetching STT usage: {str(e)}")
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
            logger.error(f"Error fetching TTS usage: {str(e)}")
            return None
        finally:
            session.close()

    def execute_sql_file(self, file):
        session = self.Session()
        try:
            session.execute(text(file.read()))
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error executing SQL file: {str(e)}")
            return False
        finally:
            session.close()

    def drop_tables(self):
        session = self.Session()
        try:
            # drop views first
            session.execute(text("DROP VIEW IF EXISTS stt_usage CASCADE"))
            session.execute(text("DROP VIEW IF EXISTS tts_usage CASCADE"))

            # drop tables
            session.execute(text("DROP TABLE IF EXISTS users CASCADE"))
            session.execute(text("DROP TABLE IF EXISTS subscriptions CASCADE"))
            session.execute(text("DROP TABLE IF EXISTS payments CASCADE"))
            session.execute(text("DROP TABLE IF EXISTS tts_activity CASCADE"))
            session.execute(text("DROP TABLE IF EXISTS stt_activity CASCADE"))
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error dropping tables: {str(e)}")
            return False
        finally:
            session.close()

    def is_user_registered(self, user_id):
        session = self.Session()
        try:
            result = session.execute(
                text("SELECT 1 FROM users WHERE user_id = :user_id"),
                {"user_id": user_id},
            ).fetchone()
            return True if result else False
        except Exception as e:
            logger.error(f"Error checking if user is registered: {str(e)}")
            return False
        finally:
            session.close()

    def register_user(self, user_id, username, first_name, last_name):
        session = self.Session()
        try:
            # add user
            new_user = User(
                user_id=user_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
            )
            session.add(new_user)
            session.commit()

            # add a new subscription
            new_subscription = Subscription(
                user_id=user_id,
                tier="free",
                start_date=date.today(),
                end_date=date.today() + timedelta(days=30),
                tts_monthly_limit_in_chars=10000,
                stt_monthly_limit_in_seconds=60 * 60,
            )
            session.add(new_subscription)
            session.commit()

            logger.debug(f"User {user_id} registered successfully.")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error registering user: {str(e)}")
            return False
        finally:
            session.close()


if __name__ == "__main__":

    # Create a DBManager instance
    db_manager = DBManager()

    if False:
        db_manager.drop_tables()
        raise Exception("Stop here")

    if True:
        # init table
        db_manager.add_user(
            user_id=1, username="test", first_name="test", last_name="test"
        )
        subscription_id = db_manager.add_subscription(
            user_id=1,
            tier="free",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            tts_limit=10000,
            stt_limit=60 * 60,
        )
        payment_id = db_manager.add_payment(
            user_id=1, subscription_id=subscription_id, amount=0, payment_method="free"
        )
        db_manager.add_tts_activity(user_id=1, character_count=1000)
        db_manager.add_stt_activity(user_id=1, duration_seconds=60)

    # init tables using mock data from mock_data.sql, also using the table classes to create the tables
    if False:
        db_manager.execute_sql_file(
            open(
                os.path.join(
                    os.path.dirname(__file__),
                    "..",
                    "..",
                    "..",
                    "postgres",
                    "mock_data.sql",
                ),
                "r",
            )
        )

    # Create views
    if True:
        db_manager.create_stt_usage_view()
        db_manager.create_tts_usage_view()

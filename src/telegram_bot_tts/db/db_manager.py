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
from datetime import date, timedelta, datetime

Base = declarative_base()

logger = logging.getLogger(__name__)


class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    username = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# create a table for free trial
class FreeTrial(Base):
    __tablename__ = "free_trials"
    free_trial_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    amount = Column(Float, nullable=False)


class Subscription(Base):
    __tablename__ = "subscriptions"
    subscription_id = Column(Integer, primary_key=True)
    payment_id = Column(Integer, ForeignKey("payments.payment_id"))
    user_id = Column(Integer, ForeignKey("users.user_id"))
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    monthly_quota = Column(Float, nullable=False)
    subscription_months = Column(Integer, nullable=False)


class Payment(Base):
    __tablename__ = "payments"
    payment_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    amount = Column(Float, nullable=False)
    payment_date = Column(DateTime(timezone=True), server_default=func.now())
    payment_method = Column(String(50))


class TextToSpeechActivity(Base):
    __tablename__ = "text_to_speech_activity"
    activity_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    used_chars = Column(Integer, nullable=False)
    cost = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())


class SpeechToTextActivity(Base):
    __tablename__ = "speech_to_text_activity"
    activity_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    used_seconds = Column(Integer, nullable=False)
    cost = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())


class DBManager:
    def __init__(self, db_url=None):
        if db_url is None:
            db_url = os.environ["DATABASE_URL"]

        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def create_tables(self):
        try:
            session = self.Session()
            Base.metadata.create_all(self.engine)
            return True
        except Exception as e:
            logger.error(f"Error creating tables: {str(e)}")
            return False
        finally:
            session.close()

    def register_user(self, user_id, first_name, last_name, username):

        try:
            # create session
            session = self.Session()
            # create new user
            user = User(
                user_id=user_id,
                first_name=first_name,
                last_name=last_name,
                username=username,
            )
            session.add(user)
            session.commit()

            # create free trial, for 7 days
            free_trial = FreeTrial(
                user_id=user_id,
                start_date=date.today(),
                end_date=date.today() + timedelta(days=7),
                amount=1,
            )
            session.add(free_trial)
            session.commit()
            return True
        except Exception as e:
            logger.error(f"Error registering user: {str(e)}")
            return False
        finally:
            session.close()

    def is_user_registered(self, user_id):
        try:
            session = self.Session()
            user = session.query(User).filter(User.user_id == user_id).first()
            return user is not None
        except Exception as e:
            logger.error(f"Error checking if user is registered: {str(e)}")
            return False
        finally:
            session.close()

    def add_payment(
        self,
        user_id: int,
        amount: float,
        payment_reference: str,
        payment_method: str,
        start_date: date,
        end_date: date,
        monthly_quota: float,
        subscription_months: int,
    ):

        try:
            session = self.Session()
            # add payment
            payment = Payment(
                payment_reference=payment_reference,
                user_id=user_id,
                amount=amount,
                payment_method=payment_method,
                payment_date=datetime.now(),
            )
            session.add(payment)
            session.commit()

            # add subscription
            subscription = Subscription(
                payment_id=payment.payment_id,
                user_id=user_id,
                amount=amount,
                start_date=start_date,
                end_date=end_date,
                monthly_quota=monthly_quota,
                subscription_months=subscription_months,
            )
            session.add(subscription)
            session.commit()

            return True
        except Exception as e:
            logger.error(f"Error adding payment: {str(e)}")
            return False
        finally:
            session.close()

    def add_text_to_speech_activity(
        self, user_id: int, used_chars: float, timestamp: datetime
    ):
        """
        Whisper $0.006 / minute (rounded to the nearest second)
        TTS $15.000 / 1M characters
        """

        try:
            session = self.Session()
            # calculate cost
            # todo: make it parametric
            cost = (used_chars / 1000000) * 15 * 1.20
            tts_activity = TextToSpeechActivity(
                user_id=user_id, used_chars=used_chars, cost=cost, timestamp=timestamp
            )
            session.add(tts_activity)
            session.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding tts activity: {str(e)}")
            return False
        finally:
            session.close()

    def add_speech_to_text_activity(
        self, user_id: int, used_seconds: float, timestamp: datetime
    ):
        """
        Whisper $0.006 / minute (rounded to the nearest second)
        TTS $15.000 / 1M characters
        """

        try:
            session = self.Session()
            # calculate cost
            # todo: make it parametric
            cost = (used_seconds / 60) * 0.006 * 1.20
            stt_activity = SpeechToTextActivity(
                user_id=user_id,
                used_seconds=used_seconds,
                cost=cost,
                timestamp=timestamp,
            )
            session.add(stt_activity)
            session.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding stt activity: {str(e)}")
            return False
        finally:
            session.close()

    def add_mock_data(self):

        # add 10 users
        try:
            for i in range(1, 11):
                self.register_user(i, f"User {i}", "Last Name", f"user{i}")

            # add 3 payments
            for i in range(1, 4):
                self.add_payment(
                    i,
                    100,
                    "Credit Card",
                    i,
                    date.today(),
                    date.today() + timedelta(days=30),
                    5,
                    1,
                )

            # add 6 tts activities
            for i in range(1, 7):
                self.add_text_to_speech_activity(i, 1000)

            # add 6 stt activities
            for i in range(1, 7):
                self.add_speech_to_text_activity(i, 1000)
        except Exception as e:
            logger.error(f"Error adding mock data: {str(e)}")
            return False

        return True

    def drop_tables(self):

        try:
            session = self.Session()
            # drop all the view first
            session.execute(text("DROP VIEW IF EXISTS user_eligibility CASCADE;"))
            session.commit()

            # drop all the tables
            Base.metadata.drop_all(self.engine)
            return True
        except Exception as e:
            logger.error(f"Error dropping tables: {str(e)}")
            return False
        finally:
            session.close()

    def create_eligibility_view(self):
        try:
            session = self.Session()
            session.execute(
                text(
                    "CREATE VIEW IF NOT EXISTS user_eligibility AS SELECT * FROM users WHERE user_id = 1;"
                )
            )
            session.commit()
            return True
        except Exception as e:
            logger.error(f"Error creating eligibility view: {str(e)}")
            return False


if __name__ == "__main__":

    # Create a DBManager instance
    db_manager = DBManager()

    if True:
        # drop tables
        db_manager.drop_tables()

        # init tables
        db_manager.create_tables()

        # add mock data
        if db_manager.add_mock_data():
            print("Mock data added")
        else:
            print("Error adding mock data")

    if True:
        # todo create view for user cost calculation
        pass

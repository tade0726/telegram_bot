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

from telegram_bot_tts.constants import VIP_USER_ID_LIST

Base = declarative_base()

logger = logging.getLogger(__name__)


class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    username = Column(String, nullable=True)
    is_vip = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# create a table for free trial
class FreeTrial(Base):
    __tablename__ = "free_trials"
    free_trial_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    amount = Column(Float, nullable=False)


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
                is_vip=user_id in VIP_USER_ID_LIST,
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
        # create view for user eligibility, all users combined will share the same quota of 3 dollars in total on a monthly basis with TTS and STT
        try:
            session = self.Session()
            session.execute(
                text(
                    """
                    CREATE OR REPLACE VIEW user_eligibility AS
                    SELECT
                        CASE
                            WHEN COALESCE(SUM(cost), 0) <= 3 THEN TRUE
                            ELSE FALSE
                        END AS is_eligible
                    FROM (
                        SELECT
                            cost
                        FROM text_to_speech_activity
                        WHERE DATE_TRUNC('month', timestamp) = DATE_TRUNC('month', CURRENT_DATE)
                        UNION ALL
                        SELECT
                            cost
                        FROM speech_to_text_activity
                        WHERE DATE_TRUNC('month', timestamp) = DATE_TRUNC('month', CURRENT_DATE)
                    ) AS combined_costs;
                    """
                )
            )
            session.commit()
            return True
        except Exception as e:
            logger.error(f"Error creating eligibility view: {str(e)}")
            return False
        finally:
            session.close()

    def check_user_eligibility(self, user_id: int) -> bool:
        # check view user_eligibility, it is a view just have one column is_eligible and one row of true or false, if true the user is eligible
        try:
            if user_id in VIP_USER_ID_LIST:
                return True

            session = self.Session()
            user_eligibility = session.execute(
                text("SELECT * FROM user_eligibility")
            ).scalar()
            return user_eligibility == True
        except Exception as e:
            logger.error(f"Error checking user eligibility: {str(e)}")
            return False
        finally:
            session.close()


if __name__ == "__main__":

    # Create a DBManager instance
    db_manager = DBManager()

    if True:
        # drop tables
        db_manager.drop_tables()

        # init tables
        db_manager.create_tables()

    if True:
        # todo create view for user cost calculation
        db_manager.create_eligibility_view()

    if False:
        # check user eligibility
        print(db_manager.check_user_eligibility(1))

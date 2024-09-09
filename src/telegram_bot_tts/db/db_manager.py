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


# create a table for free trial
class FreeTrial(Base):
    __tablename__ = "free_trials"
    free_trial_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    tts_limit = Column(Integer)
    stt_limit = Column(Integer)


class Subscription(Base):
    __tablename__ = "subscriptions"
    subscription_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    tts_monthly_limit_in_seconds = Column(Integer)
    stt_monthly_limit_in_chars = Column(Integer)


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
    seconds_used = Column(Integer, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())


class STTActivity(Base):
    __tablename__ = "stt_activity"
    stt_activity_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    chars_used = Column(Integer, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())


class DBManager:
    def __init__(self, db_url=None):
        if db_url is None:
            db_url = os.environ["DATABASE_URL"]

        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def create_tables(self):
        session = self.Session()
        try:
            Base.metadata.create_all(self.engine)
            return True
        except Exception as e:
            logger.error(f"Error creating tables: {str(e)}")
            return False
        finally:
            session.close()

    def register_user(self, user_id, first_name, last_name, username):

        # create session
        session = self.Session()

        try:
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
                tts_limit=60 * 60,
                stt_limit=10000,
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
        session = self.Session()
        try:
            user = session.query(User).filter(User.user_id == user_id).first()
            return user is not None
        except Exception as e:
            logger.error(f"Error checking if user is registered: {str(e)}")
            return False
        finally:
            session.close()

    def add_subscription(
        self,
        user_id,
        start_date,
        end_date,
        stt_monthly_limit_in_chars,
        tts_monthly_limit_in_seconds,
        amount,
        payment_id,
        payment_date,
        payment_method,
    ):
        session = self.Session()
        try:
            subscription = Subscription(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date,
                stt_monthly_limit_in_chars=stt_monthly_limit_in_chars,
                tts_monthly_limit_in_seconds=tts_monthly_limit_in_seconds,
            )
            session.add(subscription)
            session.commit()

            # add payment
            payment = Payment(
                payment_id=payment_id,
                user_id=user_id,
                subscription_id=subscription.subscription_id,
                amount=amount,
                payment_date=payment_date,
                payment_method=payment_method,
            )
            session.add(payment)
            session.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding subscription: {str(e)}")
            return False
        finally:
            session.close()

    def get_subscription(self, user_id):
        session = self.Session()
        try:
            subscription = (
                session.query(Subscription)
                .filter(Subscription.user_id == user_id)
                .first()
            )
            return subscription
        except Exception as e:
            logger.error(f"Error getting subscription: {str(e)}")
            return None
        finally:
            session.close()

    def get_payment(self, user_id):
        session = self.Session()
        try:
            payment = session.query(Payment).filter(Payment.user_id == user_id).first()
            return payment
        except Exception as e:
            logger.error(f"Error getting payment: {str(e)}")
            return None
        finally:
            session.close()

    def add_me_as_super_user(self, user_id):
        # add me as super user with no end date and no limits

        session = self.Session()
        try:
            # add me as super user with no end date and no limits
            subscription = Subscription(
                user_id=user_id,
                start_date=date.today(),
                end_date=None,
                tts_monthly_limit_in_seconds=None,
                stt_monthly_limit_in_chars=None,
            )
            session.add(subscription)
            session.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding subscription: {str(e)}")
            return False
        finally:
            session.close()

    def mock_data(self):

        try:
            # add mock users like that are new registered users, and they are in free trial, few of them has subscription

            # add 10 users
            for i in range(10):
                self.register_user(i, f"User {i}", f"User {i}", f"User {i}")

            # 30% have subscription (approximately 3 users)
            for i in range(10):
                if i % 3 == 0:
                    self.add_subscription(
                        user_id=i,
                        start_date=date.today(),
                        end_date=date.today() + timedelta(days=30),
                        tts_monthly_limit_in_seconds=1000000,
                        stt_monthly_limit_in_chars=1000000,
                        amount=100,
                        payment_id=i,
                        payment_date=date.today(),
                        payment_method="credit card",
                    )

            # add 10 tts activities
            for i in range(10):
                self.add_tts_activity(i, 1000, date.today())

            # add 10 stt activities
            for i in range(10):
                self.add_stt_activity(i, 1000, date.today())

            return True
        except Exception as e:
            logger.error(f"Error adding mock data: {str(e)}")
            return False

    def add_tts_activity(self, user_id, seconds_used, timestamp):
        session = self.Session()
        try:
            tts_activity = TTSActivity(
                user_id=user_id, seconds_used=seconds_used, timestamp=timestamp
            )
            session.add(tts_activity)
            session.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding tts activity: {str(e)}")
            return False

    def add_stt_activity(self, user_id, chars_used, timestamp):
        session = self.Session()
        try:
            stt_activity = STTActivity(
                user_id=user_id, chars_used=chars_used, timestamp=timestamp
            )
            session.add(stt_activity)
            session.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding stt activity: {str(e)}")

    def is_active_user(self, user_id):

        pass

    def drop_tables(self):

        session = self.Session()

        try:
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
        session = self.Session()
        try:
            # First, drop the existing view if it exists
            drop_view_sql = """
            DROP VIEW IF EXISTS user_eligibility;
            """
            session.execute(text(drop_view_sql))
            session.commit()

            # Now create the new view
            view_definition = """
            CREATE VIEW user_eligibility AS
            WITH user_periods AS (
                SELECT 
                    u.user_id,
                    COALESCE(s.start_date, ft.start_date) AS period_start,
                    COALESCE(s.end_date, ft.end_date) AS period_end,
                    CASE 
                        WHEN s.start_date IS NOT NULL THEN 'Subscription'
                        WHEN ft.start_date IS NOT NULL THEN 'Free Trial'
                        ELSE 'None'
                    END AS period_type,
                    COALESCE(s.tts_monthly_limit_in_seconds, ft.tts_limit) AS tts_limit,
                    COALESCE(s.stt_monthly_limit_in_chars, ft.stt_limit) AS stt_limit
                FROM users u
                LEFT JOIN subscriptions s ON u.user_id = s.user_id
                LEFT JOIN free_trials ft ON u.user_id = ft.user_id
            ),
            user_usage AS (
                SELECT 
                    up.user_id,
                    up.period_type,
                    up.period_start,
                    up.period_end,
                    up.tts_limit,
                    up.stt_limit,
                    COALESCE(SUM(ta.seconds_used) FILTER (
                        WHERE ta.timestamp >= 
                            CASE 
                                WHEN up.period_type = 'Subscription' THEN 
                                    DATE_TRUNC('month', GREATEST(up.period_start, CURRENT_DATE - INTERVAL '1 month'))
                                ELSE up.period_start
                            END
                    ), 0) AS tts_usage,
                    COALESCE(SUM(sa.chars_used) FILTER (
                        WHERE sa.timestamp >= 
                            CASE 
                                WHEN up.period_type = 'Subscription' THEN 
                                    DATE_TRUNC('month', GREATEST(up.period_start, CURRENT_DATE - INTERVAL '1 month'))
                                ELSE up.period_start
                            END
                    ), 0) AS stt_usage
                FROM user_periods up
                LEFT JOIN tts_activity ta ON up.user_id = ta.user_id
                LEFT JOIN stt_activity sa ON up.user_id = sa.user_id
                GROUP BY up.user_id, up.period_type, up.period_start, up.period_end, up.tts_limit, up.stt_limit
            )
            SELECT 
                uu.user_id,
                CASE 
                    WHEN uu.period_end >= CURRENT_DATE 
                         AND uu.tts_usage < uu.tts_limit
                         AND uu.stt_usage < uu.stt_limit
                    THEN uu.period_type || ' Active'
                    ELSE 'Not Eligible'
                END AS eligibility_status,
                uu.period_type,
                uu.period_start,
                uu.period_end,
                uu.tts_limit,
                uu.stt_limit,
                uu.tts_usage,
                uu.stt_usage
            FROM user_usage uu;
            """
            session.execute(text(view_definition))
            session.commit()
            logger.info("User eligibility view created successfully")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating user eligibility view: {str(e)}")
            return False
        finally:
            session.close()

    def is_user_eligible(self, user_id):
        session = self.Session()
        try:
            result = session.execute(
                text(
                    "SELECT eligibility_status, period_type, period_start, period_end, tts_limit, stt_limit, tts_usage, stt_usage FROM user_eligibility WHERE user_id = :user_id"
                ),
                {"user_id": user_id},
            ).fetchone()
            if result:
                (status, *_) = result
                return status.endswith("Active"), status
            return False, "User not found"
        except Exception as e:
            logger.error(f"Error checking user eligibility: {str(e)}")
            return False, "Error checking eligibility"
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

        # add mock data
        if db_manager.mock_data():
            print("Mock data added")
        else:
            print("Error adding mock data")

    if True:
        # create view
        db_manager.create_eligibility_view()

        # check if user is eligible
        is_eligible, status = db_manager.is_user_eligible(1)
        print(f"User 1 is eligible: {is_eligible}, status: {status}")

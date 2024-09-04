import pytest
from datetime import date, datetime
from unittest.mock import patch, MagicMock
from src.telegram_bot_tts.db.db_manager import DBManager, User, Subscription, Payment, TTSActivity, STTActivity

@pytest.fixture
def db_manager():
    return DBManager("sqlite:///:memory:")

def test_add_user(db_manager):
    user_id = db_manager.add_user("testuser", "test@example.com", "password_hash")
    assert user_id is not None

def test_add_subscription(db_manager):
    user_id = db_manager.add_user("testuser", "test@example.com", "password_hash")
    subscription_id = db_manager.add_subscription(
        user_id, "Basic", date.today(), date(2023, 12, 31), 1000, 60
    )
    assert subscription_id is not None

def test_add_payment(db_manager):
    user_id = db_manager.add_user("testuser", "test@example.com", "password_hash")
    subscription_id = db_manager.add_subscription(
        user_id, "Basic", date.today(), date(2023, 12, 31), 1000, 60
    )
    payment_id = db_manager.add_payment(user_id, subscription_id, 9.99, "Credit Card")
    assert payment_id is not None

def test_add_tts_activity(db_manager):
    user_id = db_manager.add_user("testuser", "test@example.com", "password_hash")
    activity_id = db_manager.add_tts_activity(user_id, 100)
    assert activity_id is not None

def test_add_stt_activity(db_manager):
    user_id = db_manager.add_user("testuser", "test@example.com", "password_hash")
    activity_id = db_manager.add_stt_activity(user_id, 30)
    assert activity_id is not None

@patch('src.telegram_bot_tts.db.db_manager.func')
def test_get_user_tts_usage(mock_func, db_manager):
    mock_func.date_trunc.return_value = datetime(2023, 5, 1)
    mock_func.coalesce.return_value = 500
    
    user_id = db_manager.add_user("testuser", "test@example.com", "password_hash")
    db_manager.add_subscription(user_id, "Basic", date.today(), date(2023, 12, 31), 1000, 60)
    db_manager.add_tts_activity(user_id, 500)

    result = db_manager.get_user_tts_usage(user_id)
    assert result is not None
    assert result.username == "testuser"
    assert result.plan_name == "Basic"
    assert result.tts_monthly_limit == 1000
    assert result.total_tts_usage == 500

@patch('src.telegram_bot_tts.db.db_manager.func')
def test_get_user_stt_usage(mock_func, db_manager):
    mock_func.date_trunc.return_value = datetime(2023, 5, 1)
    mock_func.coalesce.return_value = 30
    
    user_id = db_manager.add_user("testuser", "test@example.com", "password_hash")
    db_manager.add_subscription(user_id, "Basic", date.today(), date(2023, 12, 31), 1000, 60)
    db_manager.add_stt_activity(user_id, 30)

    result = db_manager.get_user_stt_usage(user_id)
    assert result is not None
    assert result.username == "testuser"
    assert result.plan_name == "Basic"
    assert result.stt_monthly_limit == 60
    assert result.total_stt_usage == 30




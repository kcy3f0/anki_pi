import pytest
from src.services.notification_service import NotificationService

def test_format_reminder_message():
    service = NotificationService()
    total_count = 5
    folder_data = {
        "Default": {"General": 3, "Medical": 2}
    }
    
    message = service.format_reminder_message(total_count, folder_data)
    
    assert "5" in message
    assert "Default" in message
    assert "General" in message
    assert "Medical" in message
    assert "3" in message
    assert "2" in message

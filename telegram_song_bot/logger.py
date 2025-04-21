"""
Logging module for the Telegram Song Bot.

This module provides standardized logging functionality for tracking user actions.
"""
import logging
import datetime
from typing import Optional, Any, Dict

# Configure logging format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Create logger
logger = logging.getLogger('SongBot')


def log_user_action(username: str, user_id: int, action: str, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Log a user action with standardized formatting.
    
    Args:
        username: User's Telegram username or first name
        user_id: User's Telegram ID
        action: Description of the action performed
        details: Additional details about the action (optional)
    """
    log_message = f"USER: {username} (ID: {user_id}) | ACTION: {action}"
    
    if details:
        detail_str = " | ".join([f"{k.upper()}: {v}" for k, v in details.items()])
        log_message += f" | {detail_str}"
    
    logger.info(log_message)


def log_error(error_type: str, error_message: str, user_id: Optional[int] = None) -> None:
    """
    Log an error with standardized formatting.
    
    Args:
        error_type: Type or category of error
        error_message: Error message or description
        user_id: User's Telegram ID (optional)
    """
    log_message = f"ERROR: {error_type} | MESSAGE: {error_message}"
    
    if user_id is not None:
        log_message = f"USER_ID: {user_id} | {log_message}"
    
    logger.error(log_message)


def log_system_event(event_type: str, message: str) -> None:
    """
    Log a system event with standardized formatting.
    
    Args:
        event_type: Type of system event
        message: Event details or message
    """
    logger.info(f"SYSTEM: {event_type} | {message}")
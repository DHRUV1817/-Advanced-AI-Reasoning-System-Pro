"""
Input validation utilities
"""
from typing import Any
from src.utils.logger import logger


def validate_input(text: str, max_length: int = 10000) -> tuple[bool, str]:
    """
    ✅ VALIDATE USER INPUT
    """
    if not text or not text.strip():
        return False, "Input cannot be empty"
    
    if len(text) > max_length:
        return False, f"Input exceeds maximum length of {max_length} characters"
    
    # XSS protection
    dangerous_patterns = ['<script>', 'javascript:', 'onerror=', 'onclick=']
    text_lower = text.lower()
    if any(pattern in text_lower for pattern in dangerous_patterns):
        return False, "Input contains potentially dangerous content"
    
    return True, ""


def validate_temperature(temp: float, min_temp: float = 0.0, max_temp: float = 2.0) -> tuple[bool, str]:
    """
    ✅ VALIDATE TEMPERATURE PARAMETER
    """
    if not isinstance(temp, (int, float)):
        return False, "Temperature must be a number"
    
    if not (min_temp <= temp <= max_temp):
        return False, f"Temperature must be between {min_temp} and {max_temp}"
    
    return True, ""


def validate_max_tokens(tokens: int, min_tokens: int = 100, max_tokens: int = 32000) -> tuple[bool, str]:
    """
    ✅ VALIDATE MAX TOKENS PARAMETER
    """
    if not isinstance(tokens, int):
        return False, "Max tokens must be an integer"
    
    if not (min_tokens <= tokens <= max_tokens):
        return False, f"Max tokens must be between {min_tokens} and {max_tokens}"
    
    return True, ""

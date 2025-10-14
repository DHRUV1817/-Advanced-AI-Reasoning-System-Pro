"""
Helper utility functions
"""
import hashlib
import uuid
from datetime import datetime
from typing import Optional


def generate_session_id() -> str:
    """
    🔑 GENERATE UNIQUE SESSION ID
    """
    timestamp = datetime.now().isoformat()
    random_uuid = str(uuid.uuid4())
    raw_id = f"{timestamp}-{random_uuid}"
    return hashlib.sha256(raw_id.encode()).hexdigest()


def format_timestamp(dt: Optional[datetime] = None) -> str:
    """
    📅 FORMAT TIMESTAMP
    """
    if dt is None:
        dt = datetime.now()
    return dt.strftime('%Y-%m-%d %H:%M:%S')


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    ✂️ TRUNCATE TEXT TO MAX LENGTH
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def sanitize_filename(filename: str) -> str:
    """
    🧹 SANITIZE FILENAME
    """
    import re
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    return filename[:255]

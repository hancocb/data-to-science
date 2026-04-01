from datetime import datetime, timedelta, timezone

from app.core.security import check_token_expired
from app.models.single_use_token import SingleUseToken


def test_check_token_expired_returns_true_for_old_token() -> None:
    """Token created 90 minutes ago should be expired with a 60-minute limit."""
    token = SingleUseToken()
    token.created_at = datetime.now(timezone.utc) - timedelta(minutes=90)
    assert check_token_expired(token, minutes=60) is True


def test_check_token_expired_returns_false_for_fresh_token() -> None:
    """Token created 5 minutes ago should not be expired with a 60-minute limit."""
    token = SingleUseToken()
    token.created_at = datetime.now(timezone.utc) - timedelta(minutes=5)
    assert check_token_expired(token, minutes=60) is False

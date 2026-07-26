"""Tests for validation utilities."""

import pytest
from handlers.utils.validation import (
    validate_uuid,
    validate_priority,
    validate_limit,
    validate_url,
)
from handlers.utils.errors import ValidationError


class TestValidateUUID:
    """Test UUID validation."""
    
    def test_valid_uuid(self):
        """Should accept valid UUID."""
        validate_uuid("123e4567-e89b-12d3-a456-426614174000", "test_field")
    
    def test_invalid_uuid_format(self):
        """Should reject invalid UUID format."""
        with pytest.raises(ValidationError, match="Invalid test_field format"):
            validate_uuid("not-a-uuid", "test_field")
    
    def test_invalid_uuid_length(self):
        """Should reject UUID with wrong length."""
        with pytest.raises(ValidationError, match="Invalid test_field format"):
            validate_uuid("123e4567-e89b-12d3-a456", "test_field")


class TestValidatePriority:
    """Test priority validation."""
    
    @pytest.mark.parametrize("priority", [0, 1, 2, 3, 4])
    def test_valid_priority(self, priority):
        """Should accept valid priority values."""
        validate_priority(priority)
    
    def test_invalid_priority_negative(self):
        """Should reject negative priority."""
        with pytest.raises(ValidationError, match="Priority must be 0-4"):
            validate_priority(-1)
    
    def test_invalid_priority_too_high(self):
        """Should reject priority > 4."""
        with pytest.raises(ValidationError, match="Priority must be 0-4"):
            validate_priority(5)


class TestValidateLimit:
    """Test limit validation."""
    
    def test_valid_limit(self):
        """Should accept valid limit."""
        result = validate_limit(50, max_limit=100)
        assert result == 50
    
    def test_limit_at_max(self):
        """Should accept limit at max."""
        result = validate_limit(100, max_limit=100)
        assert result == 100
    
    def test_limit_exceeds_max(self):
        """Should reject limit exceeding max."""
        with pytest.raises(ValidationError, match="Limit cannot exceed"):
            validate_limit(101, max_limit=100)
    
    def test_limit_negative(self):
        """Should reject negative limit."""
        with pytest.raises(ValidationError, match="Limit must be a positive integer"):
            validate_limit(-1, max_limit=100)
    
    def test_limit_zero(self):
        """Should reject zero limit."""
        with pytest.raises(ValidationError, match="Limit must be a positive integer"):
            validate_limit(0, max_limit=100)


class TestValidateURL:
    """Test URL validation."""
    
    def test_valid_http_url(self):
        """Should accept valid HTTP URL."""
        validate_url("http://example.com")
    
    def test_valid_https_url(self):
        """Should accept valid HTTPS URL."""
        validate_url("https://example.com/path?query=value")
    
    def test_invalid_url_no_scheme(self):
        """Should reject URL without scheme."""
        with pytest.raises(ValidationError, match="Invalid url format"):
            validate_url("example.com")
    
    def test_invalid_url_empty(self):
        """Should reject empty URL."""
        with pytest.raises(ValidationError, match="Invalid url format"):
            validate_url("")

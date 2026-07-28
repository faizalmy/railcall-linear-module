"""Tests for validation utilities."""

import pytest
from handlers.utils.validation import (
    validate_uuid,
    validate_priority,
    validate_limit,
    validate_url,
    validate_color,
    validate_iso_date,
    validate_non_empty,
    validate_comment_id,
    validate_issue_id,
    validate_resource_types,
    validate_label_id,
    validate_cycle_id,
    validate_milestone_id,
    validate_webhook_id,
    validate_initiative_id,
    validate_state_id,
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

    def test_omitted_limit_falls_back_to_the_default(self):
        """Every list command passes limit through, so None is the common path."""
        assert validate_limit(None) == 50
        assert validate_limit(None, default=10) == 10


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


class TestColorValidation:
    """Linear rejects non-hex colors; catch them before the round trip."""

    @pytest.mark.parametrize("color", ["#FF0000", "#f00", "#AbCdEf"])
    def test_accepts_hex(self, color):
        validate_color(color)

    @pytest.mark.parametrize("color", ["red", "FF0000", "#GG0000", "#FF00", "", None])
    def test_rejects_non_hex(self, color):
        with pytest.raises(ValidationError):
            validate_color(color)


class TestIsoDateValidation:
    """Cycle and milestone dates must be ISO 8601."""

    @pytest.mark.parametrize("value", [
        "2026-01-31",
        "2026-01-31T00:00:00Z",
        "2026-01-31T12:30:00+02:00",
    ])
    def test_accepts_iso(self, value):
        validate_iso_date(value, "starts_at")

    @pytest.mark.parametrize("value", ["31/01/2026", "Jan 31 2026", "", "   "])
    def test_rejects_non_iso(self, value):
        with pytest.raises(ValidationError):
            validate_iso_date(value, "starts_at")


class TestNonEmptyValidation:
    """Required text fields must carry content."""

    def test_accepts_text(self):
        validate_non_empty("Fix login", "title")

    @pytest.mark.parametrize("value", ["", "   ", None])
    def test_rejects_blank(self, value):
        with pytest.raises(ValidationError):
            validate_non_empty(value, "title")


class TestCommentIdValidation:
    """comment_id was previously accepted unchecked."""

    def test_accepts_uuid(self):
        validate_comment_id("123e4567-e89b-12d3-a456-426614174000")

    def test_rejects_garbage(self):
        with pytest.raises(ValidationError):
            validate_comment_id("not-a-uuid")


class TestIssueIdAcceptsBothForms:
    """An issue may be named by UUID or by its ENG-123 identifier.

    Linear accepts both on reads and on every issue mutation; requiring the
    UUID was this module's own restriction. The identifier is what an operator
    already has - it is in the Linear URL and on the card - so rejecting it
    sent people hunting for a UUID they had no reason to know.
    """

    UUID = "123e4567-e89b-12d3-a456-426614174000"

    def test_accepts_uuid(self):
        validate_issue_id(self.UUID)

    @pytest.mark.parametrize("identifier", ["ENG-123", "RAI-1", "A1-9999", "eng-123"])
    def test_accepts_identifier(self, identifier):
        """Lowercase included - Linear resolves eng-123 the same as ENG-123."""
        validate_issue_id(identifier)

    @pytest.mark.parametrize("bad", [
        "ENG",          # no number
        "ENG-",         # no number
        "-123",         # no team key
        "123-456",      # key must start with a letter
        "ENG 123",      # space, not a dash
        "not-a-uuid",
        "",
        None,
    ])
    def test_rejects_everything_else(self, bad):
        with pytest.raises(ValidationError, match="issue_id"):
            validate_issue_id(bad)

    def test_error_names_both_accepted_shapes(self):
        """The message is what an operator gets back through the airlock."""
        with pytest.raises(ValidationError, match="ENG-123"):
            validate_issue_id("garbage")

    def test_other_ids_still_require_a_uuid(self):
        """Only issues have a human identifier; a team key is not one."""
        with pytest.raises(ValidationError):
            validate_state_id("ENG-123")
        with pytest.raises(ValidationError):
            validate_cycle_id("ENG-123")


class TestResourceTypeValidation:
    """create_webhook's resourceTypes list reaches Linear verbatim.

    The empty-list case was covered through create_webhook; the per-item check
    was not, so a list holding a number or a blank string would have been
    caught only by Linear, one network round trip later.
    """

    def test_accepts_linear_resource_types(self):
        validate_resource_types(["Issue", "Comment"])

    def test_rejects_empty_list(self):
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_resource_types([])

    @pytest.mark.parametrize("bad", [["Issue", 42], ["Issue", ""], ["  "], [None]])
    def test_rejects_non_string_or_blank_entries(self, bad):
        with pytest.raises(ValidationError, match="Invalid resource type"):
            validate_resource_types(bad)


class TestIdValidatorsDelegate:
    """Each typed id validator is a thin wrapper over validate_uuid.

    Thin enough that they were never asserted directly - so a wrapper that
    forgot to call validate_uuid, or named the wrong field in its error, would
    pass the suite while accepting garbage in production.
    """

    VALIDATORS = [
        (validate_label_id, "label_id"),
        (validate_cycle_id, "cycle_id"),
        (validate_milestone_id, "milestone_id"),
        (validate_webhook_id, "webhook_id"),
        (validate_initiative_id, "initiative_id"),
        (validate_state_id, "state_id"),
    ]

    @pytest.mark.parametrize("validator,field", VALIDATORS)
    def test_accepts_uuid(self, validator, field):
        validator("123e4567-e89b-12d3-a456-426614174000")

    @pytest.mark.parametrize("validator,field", VALIDATORS)
    def test_rejects_garbage_and_names_the_field(self, validator, field):
        with pytest.raises(ValidationError, match=field):
            validator("ENG-123")

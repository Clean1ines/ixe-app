"""
Unit tests for the ScrapingConfig value object.
"""
import pytest
from src.application.value_objects.scraping.scraping_config import ScrapingConfig, ScrapingMode


class TestScrapingConfigCreation:
    """Tests for creating a ScrapingConfig instance."""

    def test_creation_success_defaults(self):
        """Test successful creation of a ScrapingConfig with default values."""
        config = ScrapingConfig()

        assert config.mode == ScrapingMode.SEQUENTIAL
        assert config.max_empty_pages == 2
        assert config.start_page == "init"
        assert config.max_pages is None
        assert config.force_restart is False
        assert config.parallel_workers == 3
        assert config.timeout_seconds == 30
        assert config.retry_attempts == 3
        assert config.retry_delay_seconds == 1
        assert config.user_agent == "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

    def test_creation_success_custom_values(self):
        """Test successful creation of a ScrapingConfig with custom values."""
        config = ScrapingConfig(
            mode=ScrapingMode.PARALLEL,
            max_empty_pages=5,
            start_page="1",
            max_pages=10,
            force_restart=True,
            parallel_workers=5,
            timeout_seconds=60,
            retry_attempts=1,
            retry_delay_seconds=2,
            user_agent="Custom User Agent"
        )

        assert config.mode == ScrapingMode.PARALLEL
        assert config.max_empty_pages == 5
        assert config.start_page == "1"
        assert config.max_pages == 10
        assert config.force_restart is True
        assert config.parallel_workers == 5
        assert config.timeout_seconds == 60
        assert config.retry_attempts == 1
        assert config.retry_delay_seconds == 2
        assert config.user_agent == "Custom User Agent"

    def test_creation_fails_negative_timeout(self):
        """Test that creation fails if timeout_seconds is negative."""
        with pytest.raises(ValueError, match="timeout_seconds must be positive"):
            ScrapingConfig(timeout_seconds=-1)

    def test_creation_fails_zero_timeout(self):
        """Test that creation fails if timeout_seconds is zero."""
        with pytest.raises(ValueError, match="timeout_seconds must be positive"):
            ScrapingConfig(timeout_seconds=0)

    def test_creation_fails_negative_retry_attempts(self):
        """Test that creation fails if retry_attempts is negative."""
        with pytest.raises(ValueError, match="retry_attempts cannot be negative"):
            ScrapingConfig(retry_attempts=-1)

    def test_creation_fails_negative_retry_delay(self):
        """Test that creation fails if retry_delay_seconds is negative."""
        with pytest.raises(ValueError, match="retry_delay_seconds cannot be negative"):
            ScrapingConfig(retry_delay_seconds=-1)

    def test_creation_fails_zero_max_empty_pages(self):
        """Test that creation fails if max_empty_pages is zero."""
        with pytest.raises(ValueError, match="max_empty_pages must be positive"):
            ScrapingConfig(max_empty_pages=0)

    def test_creation_fails_negative_max_pages(self):
        """Test that creation fails if max_pages is negative."""
        with pytest.raises(ValueError, match="max_pages must be positive if specified"):
            ScrapingConfig(max_pages=-1)

    def test_equality_same_values(self):
        """Test that ScrapingConfig instances with same values are equal."""
        config1 = ScrapingConfig(max_empty_pages=3, timeout_seconds=45)
        config2 = ScrapingConfig(max_empty_pages=3, timeout_seconds=45)

        assert config1 == config2
        assert hash(config1) == hash(config2)

    def test_equality_different_values(self):
        """Test that ScrapingConfig instances with different values are not equal."""
        config1 = ScrapingConfig(max_empty_pages=3, timeout_seconds=45)
        config2 = ScrapingConfig(max_empty_pages=2, timeout_seconds=45)  # Different max_empty_pages
        config3 = ScrapingConfig(max_empty_pages=3, timeout_seconds=30)  # Different timeout

        assert config1 != config2
        assert config1 != config3
        assert hash(config1) != hash(config2) # Hashes likely different if values differ
        assert hash(config1) != hash(config3) # Hashes likely different if values differ

if __name__ == "__main__":
    pytest.main(["-v", __file__])

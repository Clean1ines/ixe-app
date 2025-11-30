"""
Startup configuration validation module.
Validates critical configuration on application startup.
"""


def validate_configuration_on_startup():
    """Validate critical configuration settings on application startup."""
    try:
        # Try to import central config
        from src.core.config import config
        
        # Check if central config is available
        if hasattr(config, 'validate_config'):
            config.validate_config()
            print("✓ Configuration validated successfully")
        else:
            print("⚠ Using fallback configuration")
            
    except ImportError as e:
        print(f"⚠ Configuration validation skipped: {e}")
    except Exception as e:
        print(f"⚠ Configuration validation warning: {e}")

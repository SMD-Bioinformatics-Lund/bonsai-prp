class PrpError(Exception):
    """Base for all PRP errors."""

class ConfigError(PrpError):
    """CLI/config/profile related errors."""

class UploadError(PrpError):
    """Bonsai API / network related errors."""

class DataFormatError(PrpError):
    """Generic data/serialization errors (IO-level)."""

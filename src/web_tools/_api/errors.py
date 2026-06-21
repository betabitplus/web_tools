"""Public exceptions for `web_tools`.

Why:
    Keeps the caller-facing exception taxonomy stable and separate from
    private browser, cache, parser, and transport details.

How:
    Runtime internals translate operational failures into these public
    exceptions before they cross the package boundary. Direct caller input
    violations may still use built-in `TypeError` or `ValueError`.
"""

from __future__ import annotations

from pathlib import Path

from py_lib_runtime import preview_text


class WebToolsError(Exception):
    """Base exception for all public `web_tools` errors."""


class WebToolsConfigurationError(WebToolsError):
    """Base exception for configuration-related failures."""


class WebToolsUsageError(WebToolsError):
    """Base exception for caller input and usage failures."""


class WebToolsProviderError(WebToolsError):
    """Base exception for runtime/provider failures."""

    def __init__(self, message: str, *, cause: Exception | None = None) -> None:
        """Initialize the error with a message and optional cause."""
        self.cause = cause
        super().__init__(message)


class InvalidConfigValueError(WebToolsConfigurationError):
    """Raised when a specific config value is invalid."""

    def __init__(self, *, field: str, value: object, reason: str) -> None:
        """Initialize with field, value, and reason."""
        self.field = field
        self.value = value
        self.reason = reason
        super().__init__(f"Invalid config value for '{field}': {value}. {reason}")


class ScriptNotFoundError(WebToolsConfigurationError):
    """Raised when a required packaged script file is missing."""

    def __init__(self, *, path: Path) -> None:
        """Initialize with the missing script path."""
        self.path = path
        super().__init__(f"Required script not found at '{path}'.")


class InvalidElementIdError(WebToolsUsageError):
    """Raised when a visual element ID format is invalid."""

    def __init__(self, *, element_id: str) -> None:
        """Initialize with the invalid element ID."""
        self.element_id = element_id
        super().__init__(
            f"Invalid element id '{element_id}'. Expected 'P_N', 'T_N', or 'M_N'."
        )


class CrawlError(WebToolsProviderError):
    """Raised when URL crawling fails."""

    def __init__(
        self,
        *,
        url: str,
        reason: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        """Initialize with URL, reason, and optional cause."""
        self.url = url
        self.reason = reason
        message = f"Failed to crawl URL '{url}'."
        if reason:
            message = f"{message} Reason: {reason}"
        elif cause is not None:
            message = f"{message} Reason: {cause}"
        super().__init__(message, cause=cause)


class ConversionError(WebToolsProviderError):
    """Raised when HTML conversion fails."""

    def __init__(
        self,
        *,
        stage: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        """Initialize with conversion stage and optional cause."""
        self.stage = stage
        message = "Failed to convert HTML."
        if stage:
            message = f"{message} Stage: {stage}."
        if cause is not None and stage is None:
            message = f"{message} Reason: {cause}"
        super().__init__(message, cause=cause)


class CacheError(WebToolsProviderError):
    """Raised when cache operations fail."""

    def __init__(
        self,
        *,
        operation: str,
        url: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        """Initialize with cache operation details and optional cause."""
        self.operation = operation
        self.url = url
        message = f"Cache {operation} failed."
        if url:
            message = f"{message} URL: {url}"
        if cause is not None and url is None:
            message = f"{message} Reason: {cause}"
        super().__init__(message, cause=cause)


class QuoteError(WebToolsProviderError):
    """Raised when quoting operations fail."""

    def __init__(
        self,
        *,
        url: str,
        text: str | None = None,
        element_id: str | None = None,
        reason: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        """Initialize with context and optional cause."""
        self.url = url
        self.text = text
        self.element_id = element_id
        self.reason = reason

        message = f"Failed to quote content for URL '{url}'."
        if text:
            preview = repr(preview_text(text))
            message = f"{message} Text: {preview}."
        elif element_id:
            message = f"{message} Element ID: {element_id}."
        if reason:
            message = f"{message} Reason: {reason}"
        elif cause is not None:
            message = f"{message} Reason: {cause}"
        super().__init__(message, cause=cause)


class WebToolsValidationError(WebToolsUsageError):
    """Raised for package-specific input validation failures."""

    def __init__(self, *, cause: Exception) -> None:
        """Initialize with the underlying validation cause."""
        self.cause = cause
        super().__init__(f"Validation failed: {cause}")


class MediaDownloadError(WebToolsProviderError):
    """Raised when media download fails."""

    def __init__(
        self,
        *,
        url: str,
        reason: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        """Initialize with URL and optional cause."""
        self.url = url
        self.reason = reason
        message = f"Failed to download media from URL '{url}'."
        if reason:
            message = f"{message} Reason: {reason}"
        elif cause is not None:
            message = f"{message} Reason: {cause}"
        super().__init__(message, cause=cause)

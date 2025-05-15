"""
Common data models.

This module contains shared models used across different endpoints.
"""

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Standard error response model."""

    message: str


class TextResponse(BaseModel):
    """Response model containing a text field."""

    text: str

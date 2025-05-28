"""
Title generation data models.

This module contains models for the title generation endpoint.
"""

from pydantic import BaseModel


class GenerateTitleRequest(BaseModel):
    """Request model for the generate_title endpoint."""

    text: str

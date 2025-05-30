"""
Common data models.

This module contains shared models used across different endpoints.
"""

from typing import Any

from pydantic import BaseModel
from pydantic.config import ConfigDict


class ErrorResponse(BaseModel):
    """Standard error response model."""

    message: str


class TextResponse(BaseModel):
    """Response model containing a text field."""

    text: str


class SnakeOrAliasModel(BaseModel):
    """Base model that lets you instantiate with snake_case OR the alias."""

    def model_dump(self, *args: Any, exclude_none: bool = True, **kwargs: Any) -> dict[str, Any]:
        return super().model_dump(*args, exclude_none=exclude_none, **kwargs)

    def model_dump_json(self, *args: Any, exclude_none: bool = True, **kwargs: Any) -> str:
        return super().model_dump_json(*args, exclude_none=exclude_none, **kwargs)

    model_config = ConfigDict(validate_by_name=True, validate_by_alias=True)

"""
User-related data models.

This module contains models for user entities and related data structures.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class User(BaseModel):
    """User model representing a user entity in the database."""

    user_id: str = Field(alias="UserId")
    email: str = Field(alias="Email")
    type: Literal["regular", "guest"] = Field(alias="Type")
    password_hash: str | None = Field(alias="PasswordHash")
    created_at: str = Field(alias="CreatedAt")
    stripe_customer_id: str | None = Field(alias="StripeCustomerId")
    active_subscription_id: str | None = Field(alias="ActiveSubscriptionId")
    subscription_status: str | None = Field(alias="SubscriptionStatus")
    plan_id: str | None = Field(alias="PlanId")
    current_period_start: str | None = Field(alias="CurrentPeriodStart")
    current_period_end: str | None = Field(alias="CurrentPeriodEnd")
    cancel_at_period_end: bool = Field(alias="CancelAtPeriodEnd")

    model_config = ConfigDict(populate_by_name=True)

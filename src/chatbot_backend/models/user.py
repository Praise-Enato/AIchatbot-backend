"""
User-related data models.

This module contains models for user entities and related data structures.
"""

from typing import Literal

from pydantic import Field

from chatbot_backend.models.common import SnakeOrAliasModel


class User(SnakeOrAliasModel):
    """User model representing a user entity in the database."""

    user_id: str = Field(alias="userId")
    email: str = Field(alias="email")
    password_hash: str | None = Field(alias="passwordHash", default=None)
    source: Literal["email", "guest", "oauth"] = Field(alias="source")
    created_at: str = Field(alias="createdAt")
    provider: str | None = Field(alias="provider", default=None)
    provider_account_id: str | None = Field(alias="providerAccountId", default=None)
    stripe_customer_id: str | None = Field(alias="stripeCustomerId", default=None)
    active_subscription_id: str | None = Field(alias="activeSubscriptionId", default=None)
    subscription_status: str | None = Field(alias="subscriptionStatus", default=None)
    plan_id: str | None = Field(alias="planId", default=None)
    current_period_start: str | None = Field(alias="currentPeriodStart", default=None)
    current_period_end: str | None = Field(alias="currentPeriodEnd", default=None)
    cancel_at_period_end: bool = Field(alias="cancelAtPeriodEnd", default=False)


class CreateEmailUserRequest(SnakeOrAliasModel):
    """Request model for creating a email user."""

    email: str = Field(alias="email")
    password_hash: str = Field(alias="passwordHash")


class CreateOAuthUserRequest(SnakeOrAliasModel):
    """Request model for creating a user via OAuth."""

    email: str | None = Field(default=None, alias="email")
    provider: str = Field(alias="provider")
    provider_account_id: str = Field(alias="providerAccountId")

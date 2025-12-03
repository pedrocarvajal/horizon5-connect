from typing import Optional

from pydantic import BaseModel, Field


class UserListQueryModel(BaseModel):
    q: Optional[str] = Field(default=None, description="Search query for filtering users by name or email")
    role: Optional[str] = Field(default=None, description="Filter users by role (comma-separated)")
    per_page: Optional[int] = Field(default=15, ge=1, le=100, description="Number of results per page")
    page: Optional[int] = Field(default=1, ge=1, description="Page number")


class UserAnalyticsModel(BaseModel):
    utm_source: Optional[str] = Field(default=None)
    utm_medium: Optional[str] = Field(default=None)
    utm_campaign: Optional[str] = Field(default=None)
    utm_term: Optional[str] = Field(default=None)
    utm_content: Optional[str] = Field(default=None)
    user_agent: str = Field(description="User agent string")
    browser: Optional[str] = Field(default=None)
    browser_version: Optional[str] = Field(default=None)
    platform: Optional[str] = Field(default=None)
    device_type: Optional[str] = Field(default=None, description="Device type: desktop, mobile, or tablet")
    ip_address: Optional[str] = Field(default=None)
    referrer: Optional[str] = Field(default=None)
    landing_page: Optional[str] = Field(default=None)
    session_id: Optional[str] = Field(default=None)
    timestamp: str = Field(description="ISO 8601 timestamp")
    language: Optional[str] = Field(default=None)
    timezone: Optional[str] = Field(default=None)
    screen_resolution: Optional[str] = Field(default=None)


class UserCreateModel(BaseModel):
    name: str = Field(description="User's full name")
    email: str = Field(description="User's email address")
    password: str = Field(min_length=8, description="User's password (min 8 characters)")
    password_confirmation: str = Field(description="Password confirmation")
    role: Optional[str] = Field(default=None, description="User role (super admin only)")
    analytics: UserAnalyticsModel = Field(description="Analytics data")


class UserUpdateModel(BaseModel):
    name: Optional[str] = Field(default=None, description="User's full name")
    email: Optional[str] = Field(default=None, description="User's email address")
    password: Optional[str] = Field(default=None, min_length=8, description="New password (optional)")
    password_confirmation: Optional[str] = Field(
        default=None, description="Password confirmation (required if password is provided)"
    )
    role: Optional[str] = Field(default=None, description="User role (super admin only)")

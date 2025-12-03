from typing import Optional
from pydantic import BaseModel, Field

class AccountListQueryModel(BaseModel):
    user_id: Optional[str] = Field(default=None, description='Filter accounts by user ID')
    gateway_id: Optional[str] = Field(default=None, description='Filter accounts by gateway ID')
    is_testnet: Optional[bool] = Field(default=None, description='Filter accounts by testnet status')
    is_active: Optional[bool] = Field(default=None, description='Filter accounts by active status')
    per_page: Optional[int] = Field(default=15, ge=1, le=100, description='Number of results per page')
    page: Optional[int] = Field(default=1, ge=1, description='Page number')

class AccountCreateModel(BaseModel):
    user_id: str = Field(description='User ID')
    gateway_id: str = Field(description='Gateway ID')
    api_key: str = Field(min_length=1, description='API key (will be encrypted server-side)', repr=False)
    api_secret: str = Field(min_length=1, description='API secret (will be encrypted server-side)', repr=False)
    is_testnet: bool = Field(default=False, description='Testnet flag')
    is_active: bool = Field(default=True, description='Active status')

class AccountUpdateModel(BaseModel):
    user_id: Optional[str] = Field(default=None, description='User ID')
    gateway_id: Optional[str] = Field(default=None, description='Gateway ID')
    api_key: Optional[str] = Field(default=None, min_length=1, description='API key (will be encrypted server-side)', repr=False)
    api_secret: Optional[str] = Field(default=None, min_length=1, description='API secret (will be encrypted server-side)', repr=False)
    is_testnet: Optional[bool] = Field(default=None, description='Testnet flag')
    is_active: Optional[bool] = Field(default=None, description='Active status')

from pydantic import BaseModel
from typing import Optional as Opt


class CaptchaRequiredRequest(BaseModel):
    captcha_token: str


class UserLoginRequest(CaptchaRequiredRequest):
    chime_id: str
    site_password: str


class BaseResponse(BaseModel):
    code: int
    message: Opt[str] = None


class UserLoginData(BaseModel):
    user_id: str
    user_name: str


class UserLoginResponse(BaseResponse):
    data: Opt[UserLoginData] = None


class GenerateRequest(CaptchaRequiredRequest):
    user_id: str
    filter: Opt[str] = None


class GenerateResponse(BaseResponse):
    data: Opt[str] = None

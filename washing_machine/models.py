from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime


class BaseRequest(BaseModel):
    userId: int


class AuthRequest(BaseRequest):
    segaIdAuthKey: Optional[Literal[""]] = ""


class GetUserPreviewRequest(AuthRequest):
    pass


class GetUserPreviewResponse(BaseModel):
    userId: int
    userName: str
    isLogin: bool
    lastGameId: Optional[int]
    lastRomVersion: str
    lastDataVersion: str
    lastLoginDate: datetime
    lastPlayDate: datetime
    playerRating: int
    nameplateId: int
    iconId: int
    trophyId: int
    isNetMember: int
    isInherit: bool
    totalAwake: int
    dispRate: int
    dailyBonusDate: datetime
    headPhoneVolume: Optional[int]
    banState: int


class UserMusicDetail(BaseModel):
    musicId: int
    level: int
    playCount: int
    achievement: int
    comboStatus: int
    syncStatus: int
    deluxscoreMax: int
    scoreRank: int
    extNum1: int
    extNum2: Optional[int | None] = None


class IndexedRequest(BaseRequest):
    nextIndex: int
    maxCount: int


class IndexedResponse(BaseModel):
    userId: Optional[int | None] = None
    length: int
    nextIndex: int


class UserMusic(BaseModel):
    length: int
    userMusicDetailList: Optional[list[UserMusicDetail] | None] = []


class GetUserMusicRequest(IndexedRequest):
    pass


class GetUserMusicResponse(IndexedResponse):
    userMusicList: Optional[list[UserMusic] | None] = []

from fastapi import APIRouter
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from os import environ as env
import base64
from aiohttp import request
import unicodedata
from io import BytesIO

from models import *
import allnet as alls
import washing_machine as wm
import best50 as b50

router = APIRouter(prefix="/api")

AES_KEY = env.get("AES_KEY").encode()
AES_IV = env.get("AES_IV").encode()


def to_half(input_string: str) -> str:
    return unicodedata.normalize("NFKC", input_string)


def encrypt_aes(data: bytes) -> bytes:
    cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
    data = pad(data, AES.block_size)
    return cipher.encrypt(data)


def decrypt_aes(data: bytes) -> bytes:
    cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
    return unpad(cipher.decrypt(data), AES.block_size)


async def turnstile_verify(token: str) -> bool:
    async with request(
            method="POST",
            url="https://challenges.cloudflare.com/turnstile/v0/siteverify",
            data=f"secret={env.get('TURNSTILE_SECRET')}&response={token}",
            headers={"Content-Type": "application/x-www-form-urlencoded"}
    ) as resp:
        return (await resp.json())["success"]


@router.post("/user_login")
async def user_login_api(req: UserLoginRequest) -> UserLoginResponse:
    if not await turnstile_verify(req.captcha_token):
        return UserLoginResponse(code=6, message="验证码验证失败")

    if req.site_password != env.get("SITE_PASSWORD"):
        return UserLoginResponse(code=7, message="密码错误")

    try:
        user_id: int = await alls.api.qrcode_to_user_id(req.chime_id)
    except alls.exc.QRCodeInvalidError:
        return UserLoginResponse(code=1, message="无效的二维码")
    except alls.exc.QRCodeExpiredError:
        return UserLoginResponse(code=2, message="二维码已过期")
    except alls.exc.ChimeBadDataError:
        return UserLoginResponse(code=3, message="密钥不合法，请联系站点管理员")
    except Exception as e:
        return UserLoginResponse(code=4, message=f"未知错误，请联系站点管理员")

    try:
        resp = await wm.api.get_user_preview_api(user_id)
    except Exception as e:
        return UserLoginResponse(code=5, message="未知错误，可能是用户未游玩过本游戏")

    return UserLoginResponse(
        code=0,
        data=UserLoginData(
            user_id=base64.b64encode(encrypt_aes(str(user_id).encode())).decode(),
            user_name=to_half(resp.userName)
        )
    )


@router.post("/generate")
async def generate_best50_api(req: GenerateRequest) -> GenerateResponse:
    if not await turnstile_verify(req.captcha_token):
        return GenerateResponse(code=1, message="验证码验证失败")

    user_id = int(decrypt_aes(base64.b64decode(req.user_id)).decode())

    combo_condition, sync_condition = None, None

    if req.filter in ['fc', 'fcp', 'ap', 'app']:
        combo_condition = b50.models.COMBO_ID_TO_NAME_NULLABLE.index(req.filter)

    if req.filter in ['fs', 'fsp', 'fsd', 'fsdp']:
        sync_condition = b50.models.SYNC_ID_TO_NAME_NULLABLE.index(req.filter)

    user_preview = await wm.api.get_user_preview_api(user_id)

    user_music_detail_list: list[wm.models.UserMusicDetail] = []
    next_index: int | None = None
    while next_index is None or next_index != 0:
        user_music_response = await wm.api.get_user_music_api(user_id, next_index or 0)
        next_index = user_music_response.nextIndex
        if user_music_response.userMusicList is not None:
            for music in user_music_response.userMusicList:
                if music.userMusicDetailList is not None:
                    for detail in music.userMusicDetailList:
                        if detail.musicId > 100000:
                            # 宴谱不计入总 rating
                            continue
                        if detail.playCount > 0:
                            if combo_condition is not None and detail.comboStatus < combo_condition:
                                continue
                            if sync_condition is not None and detail.syncStatus < sync_condition:
                                continue
                            user_music_detail_list.append(detail)
    _, best35_charts, best15_charts = (b50.utils.calculate_best50(user_music_detail_list))
    best50_img = b50.generator.generate50(
        best35_charts, best15_charts, user_preview.userName
    )
    photo_bytes = BytesIO()
    best50_img.save(photo_bytes, format='PNG')

    data_uri = 'data:image/png;base64,' + base64.b64encode(photo_bytes.getvalue()).decode('utf-8')

    return GenerateResponse(code=0, data=data_uri)

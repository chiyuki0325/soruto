import unicodedata
import washing_machine as wm
from math import floor
from typing import Literal
from data.music_db import music_db
from data.music_decimals import music_decimals
from dataclasses import dataclass
from best50 import models


def to_half(input_string: str) -> str:
    return unicodedata.normalize("NFKC", input_string)


def get_rank_factor(achievement: int) -> float:
    thresholds = {
        1005000: 22.4,  # 1005000 - 1009999
        1004999: 22.2,  # 1004999 - 1005000
        1000000: 21.6,  # 1000000 - 1004999
        999999: 21.4,  # 999999 - 1000000
        995000: 21.1,  # 995000 - 999999
        990000: 20.8,  # 990000 - 995000
        989999: 20.6,  # 989999 - 990000
        980000: 20.3,  # 980000 - 989999
        970000: 20,  # 970000 - 980000
        969999: 17.6,  # 969999 - 970000
        940000: 16.8,  # 940000 - 970000
        900000: 15.2,  # 900000 - 940000
        800000: 13.6,  # 800000 - 900000
        750000: 12,  # 750000 - 800000
        700000: 11.2,  # 700000 - 750000
        600000: 9.6,  # 600000 - 700000
        500000: 8,  # 500000 - 600000
        400000: 6.4,  # 400000 - 500000
        300000: 4.8,  # 300000 - 400000
        200000: 3.2,  # 200000 - 300000
        100000: 1.6,  # 100000 - 200000
        0: 0,  # 0 - 100000
    }
    for threshold, factor in thresholds.items():
        if achievement >= threshold:
            return factor


def calculate_single_rating(
        music_detail: wm.models.UserMusicDetail,
) -> float:
    if music_detail.achievement > 1005000:
        achievement = 1005000
    else:
        achievement = music_detail.achievement
    return (
            (achievement / 1000000) *  # 达成率
            get_rank_factor(achievement) *  # 达成率系数
            music_decimals[music_detail.musicId][music_detail.level]  # 乐谱定数
    )


@dataclass
class Chart:
    id: int
    level: int
    chart_type: Literal['dx', 'standard']
    achievement: int
    combo_state: Literal[
        "fc", "fcp", "ap", "app"
    ]
    score_rank: Literal[
        "d", "c", "b", "bb", "bbb", "a", "aa", "aaa", "s", "sp", "ss", "ssp", "sss", "sssp"
    ]
    rating: float

    def __eq__(self, other):
        return self.rating == other.rating

    def __lt__(self, other):
        return self.rating < other.rating


def calculate_best50(
        music_details: list[wm.models.UserMusicDetail]
) -> (
        int,  # rating
        list,  # best35_charts
        list  # best15_charts
):
    music_id_list = music_decimals.keys()
    standard_charts, deluxe_charts = [], []

    # 分类 SD 和 DX 乐谱
    for music in music_details:
        if music.musicId not in music_id_list:
            continue
        chart = Chart(
            id=music.musicId,
            level=music.level,
            achievement=music.achievement,
            combo_state=models.COMBO_ID_TO_NAME_NULLABLE[music.comboStatus],
            score_rank=models.RATE_ID_TO_NAME[music.scoreRank],
            rating=calculate_single_rating(music),
            chart_type='standard' if music.musicId < 10000 else 'dx'
        )
        if music_db[music.musicId]['version'] < 21:
            standard_charts.append(chart)
        else:
            deluxe_charts.append(chart)
    best35_charts = sorted(standard_charts, key=lambda x: (x.rating, x.achievement), reverse=True)[:35]
    best15_charts = sorted(deluxe_charts, key=lambda x: (x.rating, x.achievement), reverse=True)[:15]

    total_rating = 0
    for chart in best35_charts:
        total_rating += floor(chart.rating)
    for chart in best15_charts:
        total_rating += floor(chart.rating)

    return total_rating, best35_charts, best15_charts

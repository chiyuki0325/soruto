# Modified from https://github.com/Diving-Fish/Chiyuki-Bot

from typing import List
from os import environ as env

from PIL import Image, ImageDraw, ImageFont, ImageFilter

from pathlib import Path
from best50.utils import Chart, to_half
from data.music_db import music_db
from data.music_decimals import music_decimals

# 角标颜色，绿黄红紫白
LEVEL_COLOR = [(69, 193, 36), (255, 186, 1), (255, 90, 102), (134, 49, 200), (217, 197, 233)]
FONT_NAME = './assets/font.ttf'
font_12 = ImageFont.truetype(FONT_NAME, 12, encoding='utf-8')
font_14 = ImageFont.truetype(FONT_NAME, 14, encoding='utf-8')
font_15 = ImageFont.truetype(FONT_NAME, 15, encoding='utf-8')
font_16 = ImageFont.truetype(FONT_NAME, 16, encoding='utf-8')
font_18 = ImageFont.truetype(FONT_NAME, 18, encoding='utf-8')


class BestList(object):

    @staticmethod
    def build(max_len: int, charts: List[Chart]):
        best_list = BestList(max_len)
        best_list.data = charts
        return best_list

    def __init__(self, size: int):
        self.data: List[Chart] = []
        self.size = size

    def push(self, elem: Chart):
        if len(self.data) >= self.size and elem < self.data[-1]:
            return
        self.data.append(elem)
        self.data.sort()
        self.data.reverse()
        while len(self.data) > self.size:
            del self.data[-1]

    def pop(self):
        del self.data[-1]

    def __str__(self):
        return '[\n\t' + ', \n\t'.join([str(ci) for ci in self.data]) + '\n]'

    def __len__(self):
        return len(self.data)

    def __getitem__(self, index):
        return self.data[index]


class DrawBest(object):

    def __init__(self, sd_best: BestList, dx_best: BestList, username: str):
        self.sd_best: BestList = sd_best
        self.dx_best: BestList = dx_best
        self.username = to_half(username)
        self.sd_rating: int = 0
        self.dx_rating: int = 0
        for sd in sd_best:
            self.sd_rating += int(sd.rating)
        for dx in dx_best:
            self.dx_rating += int(dx.rating)
        self.total_rating = self.sd_rating + self.dx_rating
        self.assets = Path('assets')
        self.img = Image.open(self.assets / 'common/background.png').convert('RGBA')
        self.ROWS_IMG = [2]
        for i in range(6):
            self.ROWS_IMG.append(116 + 96 * i)
        self.COLUMNS_IMG = []
        for i in range(8):
            self.COLUMNS_IMG.append(2 + 138 * i)
        for i in range(4):
            self.COLUMNS_IMG.append(988 + 138 * i)
        self.draw()

    def _get_char_width(self, o) -> int:
        widths = [
            (126, 1), (159, 0), (687, 1), (710, 0), (711, 1), (727, 0), (733, 1), (879, 0), (1154, 1), (1161, 0),
            (4347, 1), (4447, 2), (7467, 1), (7521, 0), (8369, 1), (8426, 0), (9000, 1), (9002, 2), (11021, 1),
            (12350, 2), (12351, 1), (12438, 2), (12442, 0), (19893, 2), (19967, 1), (55203, 2), (63743, 1),
            (64106, 2), (65039, 1), (65059, 0), (65131, 2), (65279, 1), (65376, 2), (65500, 1), (65510, 2),
            (120831, 1), (262141, 2), (1114109, 1),
        ]
        if o == 0xe or o == 0xf:
            return 0
        for num, wid in widths:
            if o <= num:
                return wid
        return 1

    def _column_width(self, s: str):
        res = 0
        for ch in s:
            res += self._get_char_width(ord(ch))
        return res

    def _change_column_width(self, s: str, len: int) -> str:
        res = 0
        sList = []
        for ch in s:
            res += self._get_char_width(ord(ch))
            if res <= len:
                sList.append(ch)
        return ''.join(sList)

    def _resize_pic(self, img: Image.Image, time: float):
        return img.resize((int(img.size[0] * time), int(img.size[1] * time)))

    def _get_rating_pic(self) -> Path:
        if self.total_rating < 1000:
            num = 'white'
        elif self.total_rating < 2000:
            num = 'blue'
        elif self.total_rating < 4000:
            num = 'green'
        elif self.total_rating < 7000:
            num = 'orange'
        elif self.total_rating < 10000:
            num = 'red'
        elif self.total_rating < 12000:
            num = 'purple'
        elif self.total_rating < 13000:
            num = 'bronze'
        elif self.total_rating < 14000:
            num = 'silver'
        elif self.total_rating < 14500:
            num = 'gold'
        elif self.total_rating < 15000:
            num = 'gold_2'
        else:
            num = 'rainbow'
        return self.assets / f'rating/{num}.png'

    def _get_shougou_pic(self) -> Path:
        if self.total_rating < 12000:
            num = 'normal'
        elif self.total_rating < 13000:
            num = 'bronze'
        elif self.total_rating < 14000:
            num = 'silver'
        elif self.total_rating < 15000:
            num = 'gold'
        else:
            num = 'rainbow'
        return self.assets / f'title/{num}.png'

    def _draw_rating(self, rating_base_image: Image.Image):
        # 在 rating 上绘制数字
        COLOUMS_RATING = [86, 100, 115, 130, 145]
        theRa = self.total_rating
        i = 4
        while theRa:
            digit = theRa % 10
            theRa = theRa // 10
            digitImg = Image.open(self.assets / f'rating_num/{digit}.png').convert('RGBA')
            digitImg = self._resize_pic(digitImg, 0.6)
            rating_base_image.paste(digitImg, (COLOUMS_RATING[i] - 2, 9), mask=digitImg.split()[3])
            i = i - 1
        return rating_base_image

    def _draw_best_list(self, img: Image.Image, sd_best: BestList, dx_best: BestList):
        item_width = 131
        item_height = 88
        levelTriagle = [(item_width, 0), (item_width - 27, 0), (item_width, 27)]

        imgDraw = ImageDraw.Draw(img)

        # SD
        for num in range(0, len(sd_best)):
            i = num // 7
            j = num % 7
            chart: Chart = sd_best[num]

            # 绘制封面
            cover_path = self.assets / f'jacket/{chart.id % 10000}.png'
            if not cover_path.exists():
                cover_path = self.assets / 'jacket/0.png'
            temp = Image.open(cover_path).convert('RGB')
            temp = self._resize_pic(temp, item_width / temp.size[0])
            temp = temp.crop((0, (temp.size[1] - item_height) / 2, item_width, (temp.size[1] + item_height) / 2))
            temp = temp.filter(ImageFilter.GaussianBlur(3))
            temp = temp.point(lambda p: int(p * 0.72))

            # 绘制乐曲名
            temp_draw = ImageDraw.Draw(temp)
            temp_draw.polygon(levelTriagle, LEVEL_COLOR[chart.level])  # 难度角标
            song_name = music_db[chart.id]['name']
            if self._column_width(song_name) > 14:
                # 如果乐曲名过长，截断
                song_name = self._change_column_width(song_name, 12) + '...'

            # 乐曲名和达成率
            temp_draw.text((8, 6), song_name, 'white', font_15)
            temp_draw.text((7, 28), f'{"%.4f" % (chart.achievement / 10000)}%', 'white', font_12)

            # 评级
            rank_img = Image.open(self.assets / f'rank/{chart.score_rank}.png').convert('RGBA')
            rank_img = self._resize_pic(rank_img, 0.3)
            temp.paste(rank_img, (72, 30), rank_img.split()[3])

            # FC / AP
            if chart.combo_state is not None:
                combo_img = Image.open(self.assets / f'combo/{chart.combo_state}.png').convert('RGBA')
                combo_img = self._resize_pic(combo_img, 0.45)
                temp.paste(combo_img, (103, 25), combo_img.split()[3])

            # 定数
            chart_decimal = music_decimals[chart.id][chart.level]
            temp_draw.text((8, 44), f'定数: {chart_decimal} -> {int(chart.rating)}', 'white',
                           font_12)
            temp_draw.text((8, 60), f'#{num + 1}', 'white', font_18)

            # 绘制到整体图
            recBase = Image.new('RGBA', (item_width, item_height), (0, 0, 0, 170))
            recBase = recBase.point(lambda p: int(p * 0.8))
            img.paste(recBase, (self.COLUMNS_IMG[j] + 5, self.ROWS_IMG[i + 1] + 5))
            img.paste(temp, (self.COLUMNS_IMG[j] + 4, self.ROWS_IMG[i + 1] + 4))

        for num in range(len(sd_best), sd_best.size):
            # 不足 35 的话就填充
            i = num // 7
            j = num % 7
            temp = Image.open(self.assets / 'jacket/0.png').convert('RGB')
            temp = self._resize_pic(temp, item_width / temp.size[0])
            temp = temp.crop((0, (temp.size[1] - item_height) / 2, item_width, (temp.size[1] + item_height) / 2))
            temp = temp.filter(ImageFilter.GaussianBlur(1))
            img.paste(temp, (self.COLUMNS_IMG[j] + 4, self.ROWS_IMG[i + 1] + 4))

        # DX
        for num in range(0, len(dx_best)):
            i = num // 3
            j = num % 3
            chart: Chart = dx_best[num]

            # 绘制封面
            cover_path = self.assets / f'jacket/{chart.id % 10000}.png'
            if not cover_path.exists():
                cover_path = self.assets / 'jacket/0.png'
            temp = Image.open(cover_path).convert('RGB')
            temp = self._resize_pic(temp, item_width / temp.size[0])
            temp = temp.crop((0, (temp.size[1] - item_height) / 2, item_width, (temp.size[1] + item_height) / 2))
            temp = temp.filter(ImageFilter.GaussianBlur(3))
            temp = temp.point(lambda p: int(p * 0.72))

            # 绘制乐曲名
            temp_draw = ImageDraw.Draw(temp)
            temp_draw.polygon(levelTriagle, LEVEL_COLOR[chart.level])  # 难度角标
            song_name = music_db[chart.id]['name']
            if self._column_width(song_name) > 14:
                # 如果乐曲名过长，截断
                song_name = self._change_column_width(song_name, 12) + '...'

            # 乐曲名和达成率
            temp_draw.text((8, 6), song_name, 'white', font_15)
            temp_draw.text((7, 28), f'{"%.4f" % (chart.achievement / 10000)}%', 'white', font_12)

            # 评级
            rank_img = Image.open(self.assets / f'rank/{chart.score_rank}.png').convert('RGBA')
            rank_img = self._resize_pic(rank_img, 0.3)
            temp.paste(rank_img, (72, 30), rank_img.split()[3])

            # FC / AP
            if chart.combo_state is not None:
                combo_img = Image.open(self.assets / f'combo/{chart.combo_state}.png').convert('RGBA')
                combo_img = self._resize_pic(combo_img, 0.45)
                temp.paste(combo_img, (103, 25), combo_img.split()[3])

            # 定数
            chart_decimal = music_decimals[chart.id][chart.level]
            temp_draw.text((8, 44), f'定数: {chart_decimal} -> {int(chart.rating)}', 'white',
                           font_12)
            temp_draw.text((8, 60), f'#{num + 1}', 'white', font_18)

            # 绘制到整体图
            recBase = Image.new('RGBA', (item_width, item_height), (0, 0, 0, 170))
            recBase = recBase.point(lambda p: int(p * 0.8))
            img.paste(recBase, (self.COLUMNS_IMG[j + 8] + 5, self.ROWS_IMG[i + 1] + 5))
            img.paste(temp, (self.COLUMNS_IMG[j + 8] + 4, self.ROWS_IMG[i + 1] + 4))

        for num in range(len(dx_best), dx_best.size):
            # 不足 15 的话就填充
            i = num // 3
            j = num % 3
            temp = Image.open(self.assets / 'jacket/0.png').convert('RGB')
            temp = self._resize_pic(temp, item_width / temp.size[0])
            temp = temp.crop((0, (temp.size[1] - item_height) / 2, item_width, (temp.size[1] + item_height) / 2))
            temp = temp.filter(ImageFilter.GaussianBlur(1))
            img.paste(temp, (self.COLUMNS_IMG[j + 8] + 4, self.ROWS_IMG[i + 1] + 4))

    def draw(self):
        # 游戏 logo
        washing_machine_logo = Image.open(self.assets / 'common/game_title.png').convert('RGBA')
        washing_machine_logo = self._resize_pic(washing_machine_logo, 0.7)
        self.img.paste(washing_machine_logo, (-45, 7), mask=washing_machine_logo.split()[3])

        # 评级
        rating_img = Image.open(self._get_rating_pic()).convert('RGBA')
        rating_img = self._draw_rating(rating_img)
        rating_img = self._resize_pic(rating_img, 0.85)
        self.img.paste(rating_img, (140, 8), mask=rating_img.split()[3])

        namePlateImg = Image.open(self.assets / 'common/UI_TST_PlateMask.png').convert('RGBA')
        namePlateImg = namePlateImg.resize((285, 40))
        namePlateDraw = ImageDraw.Draw(namePlateImg)

        # 绘制玩家名
        font_player_name = ImageFont.truetype(FONT_NAME, 28, encoding='utf-8')
        namePlateDraw.text((12, 4), ' '.join(list(self.username)), 'black', font_player_name)
        nameDxImg = Image.open(self.assets / 'common/UI_CMN_Name_DX.png').convert('RGBA')
        nameDxImg = self._resize_pic(nameDxImg, 0.9)
        namePlateImg.paste(nameDxImg, (230, 4), mask=nameDxImg.split()[3])
        self.img.paste(namePlateImg, (140, 40), mask=namePlateImg.split()[3])

        # 绘制总 rating
        shougouImg = Image.open(self._get_shougou_pic()).convert('RGBA')
        shougouDraw = ImageDraw.Draw(shougouImg)
        playCountInfo = f'旧版本: {self.sd_rating} + 2024: {self.dx_rating} = {self.total_rating}'
        shougouImgW, shougouImgH = shougouImg.size
        playCountInfoW, playCountInfoH = shougouDraw.textsize(playCountInfo, font_14)
        textPos = ((shougouImgW - playCountInfoW - font_14.getoffset(playCountInfo)[0]) / 2, 5)
        # 绘制阴影
        shougouDraw.text((textPos[0] - 1, textPos[1]), playCountInfo, 'black', font_14)
        shougouDraw.text((textPos[0] + 1, textPos[1]), playCountInfo, 'black', font_14)
        shougouDraw.text((textPos[0], textPos[1] - 1), playCountInfo, 'black', font_14)
        shougouDraw.text((textPos[0], textPos[1] + 1), playCountInfo, 'black', font_14)
        shougouDraw.text((textPos[0] - 1, textPos[1] - 1), playCountInfo, 'black', font_14)
        shougouDraw.text((textPos[0] + 1, textPos[1] - 1), playCountInfo, 'black', font_14)
        shougouDraw.text((textPos[0] - 1, textPos[1] + 1), playCountInfo, 'black', font_14)
        shougouDraw.text((textPos[0] + 1, textPos[1] + 1), playCountInfo, 'black', font_14)
        shougouDraw.text(textPos, playCountInfo, 'white', font_14)
        shougouImg = self._resize_pic(shougouImg, 1.05)
        self.img.paste(shougouImg, (140, 83), mask=shougouImg.split()[3])

        self._draw_best_list(self.img, self.sd_best, self.dx_best)

        authorBoardImg = Image.open(self.assets / 'common/UI_CMN_MiniDialog_01.png').convert('RGBA')
        authorBoardImg = self._resize_pic(authorBoardImg, 0.35)
        authorBoardDraw = ImageDraw.Draw(authorBoardImg)
        authorBoardDraw.text((23, 28), '   Generated By\n' + env.get('GENERATOR_NAME', '      ソルト'), 'black', font_14)
        self.img.paste(authorBoardImg, (1224, 19), mask=authorBoardImg.split()[3])

        dxImg = Image.open(self.assets / 'common/dx.png').convert('RGBA')
        self.img.paste(dxImg, (988, 65 + 15), mask=dxImg.split()[3])
        sdImg = Image.open(self.assets / 'common/standard.png').convert('RGBA')
        self.img.paste(sdImg, (850, 65 + 15), mask=sdImg.split()[3])

        # self.img.show()

    def get_final_img(self):
        return self.img


def generate50(best35: List[Chart], best15: List[Chart], username: str) -> Image.Image:
    pic = DrawBest(
        BestList.build(35, best35),
        BestList.build(15, best15),
        username
    ).get_final_img()
    return pic

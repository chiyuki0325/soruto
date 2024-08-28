import json

music_decimals: dict[int, dict[int, float]] = {}

__all__ = ['music_decimals']

with open('data/music_decimals.json', 'r', encoding='utf-8') as f:
    j = json.loads(f.read())
    for k, v in j.items():
        music_decimals[int(k)] = {
            int(kk): vv
            for kk, vv in v.items()
        }

if __name__ == '__main__':
    print(music_decimals)

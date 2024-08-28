import json


music_db: dict[int, dict[str, int | str]]

__all__ = ['music_db']

with open('data/music_db.json', 'r', encoding='utf-8') as f:
    j = json.loads(f.read())
    music_db = {int(k): v for k, v in j.items()}

if __name__ == '__main__':
    print(music_db)

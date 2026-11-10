"""只保存评价元数据；默认位于用户数据目录之外于 Git 仓库。"""
import json
import os
from pathlib import Path
import sqlite3
from contextlib import closing


def default_path():
    return Path(os.environ.get('LOCALAPPDATA', str(Path.home()/'.local/share')))/'NaxiAIStudio'/'learning.sqlite3'


class LearningRecords:
    def __init__(self, path=None):
        self.path = Path(path) if path else default_path()

    def save(self, record):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with closing(sqlite3.connect(self.path,timeout=10)) as conn, conn:
            conn.execute('CREATE TABLE IF NOT EXISTS evaluations (submission_id TEXT PRIMARY KEY, record_json TEXT NOT NULL)')
            conn.execute('INSERT OR IGNORE INTO evaluations VALUES (?,?)',
                         (record['submission_id'],json.dumps(record,ensure_ascii=False,allow_nan=False)))

    def recent(self, limit=20):
        if not self.path.exists():
            return []
        with closing(sqlite3.connect(self.path,timeout=10)) as conn:
            rows=conn.execute('SELECT record_json FROM evaluations ORDER BY rowid DESC LIMIT ?', (limit,)).fetchall()
        return [json.loads(row[0]) for row in rows]

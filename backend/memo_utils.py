#!/usr/bin/env python3
"""Memo extraction helpers for Star Office backend.

Reads and sanitizes daily memo content from memory/*.md for the yesterday-memo API.
"""

from __future__ import annotations

from datetime import datetime, timedelta
import random
import re


def get_yesterday_date_str() -> str:
    """Return yesterday's date as YYYY-MM-DD."""
    yesterday = datetime.now() - timedelta(days=1)
    return yesterday.strftime("%Y-%m-%d")


def sanitize_content(text: str) -> str:
    """Redact PII and sensitive patterns (OpenID, paths, IPs, email, phone) for safe display."""
    text = re.sub(r'ou_[a-f0-9]+', '[使用者]', text)
    text = re.sub(r'user_id="[^"]+"', 'user_id="[隱藏]"', text)
    text = re.sub(r'/root/[^"\s]+', '[路徑]', text)
    text = re.sub(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', '[IP]', text)

    text = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '[郵箱]', text)
    text = re.sub(r'1[3-9]\d{9}', '[手機號]', text)

    return text


def extract_memo_from_file(file_path: str) -> str:
    """Extract display-safe memo text from a memory markdown file; sanitizes and truncates with a short fallback."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 提取真實內容，不做過度包裝
        lines = content.strip().split("\n")

        # 提取核心要點
        core_points = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith("#"):
                continue
            if line.startswith("- "):
                core_points.append(line[2:].strip())
            elif len(line) > 10:
                core_points.append(line)

        if not core_points:
            return "「昨日無事記錄」\n\n若有恆，何必三更眠五更起；最無益，莫過一日曝十日寒。"

        # 從核心內容中提取 2-3 個關鍵點
        selected_points = core_points[:3]

        # 睿智語錄庫
        wisdom_quotes = [
            "「工欲善其事，必先利其器。」",
            "「不積跬步，無以至千里；不積小流，無以成江海。」",
            "「知行合一，方可致遠。」",
            "「業精於勤，荒於嬉；行成於思，毀於隨。」",
            "「路漫漫其修遠兮，吾將上下而求索。」",
            "「昨夜西風凋碧樹，獨上高樓，望盡天涯路。」",
            "「衣帶漸寬終不悔，為伊消得人憔悴。」",
            "「眾裡尋他千百度，驀然回首，那人卻在，燈火闌珊處。」",
            "「世事洞明皆學問，人情練達即文章。」",
            "「紙上得來終覺淺，絕知此事要躬行。」"
        ]

        quote = random.choice(wisdom_quotes)

        # 組合內容
        result = []

        # 新增核心內容
        if selected_points:
            for point in selected_points:
                # 隱私清理
                point = sanitize_content(point)
                # 截斷過長的內容
                if len(point) > 40:
                    point = point[:37] + "..."
                # 每行最多 20 字
                if len(point) <= 20:
                    result.append(f"· {point}")
                else:
                    # 按 20 字切分
                    for j in range(0, len(point), 20):
                        chunk = point[j:j+20]
                        if j == 0:
                            result.append(f"· {chunk}")
                        else:
                            result.append(f"  {chunk}")

        # 新增睿智語錄
        if quote:
            if len(quote) <= 20:
                result.append(f"\n{quote}")
            else:
                for j in range(0, len(quote), 20):
                    chunk = quote[j:j+20]
                    if j == 0:
                        result.append(f"\n{chunk}")
                    else:
                        result.append(chunk)

        return "\n".join(result).strip()

    except Exception as e:
        print(f"extract_memo_from_file failed: {e}")
        return "「昨日記錄載入失敗」\n\n「往者不可諫，來者猶可追。」"

#!/usr/bin/env python3
# utils.py - utilitas nomor & helper umum

import random

from useragents import USER_AGENTS


def normalize(phone: str) -> str:
    """Normalisasi nomor ke format 62xxxxxxxxxx. Return '' kalau tidak valid."""
    n = phone.strip().replace(" ", "").replace("-", "").replace("+", "")
    if n.startswith("08"):
        n = "62" + n[1:]
    elif n.startswith("8"):
        n = "62" + n
    if not n.startswith("62"):
        return ""
    if not n[3:].isdigit() or not (9 <= len(n) <= 15):
        return ""
    return n


def fmt_08(n62: str) -> str:
    return "0" + n62[2:]


def fmt_plus(n62: str) -> str:
    return "+" + n62


def fmt_nocode(n62: str) -> str:
    return n62[2:]


def ua() -> str:
    return random.choice(USER_AGENTS)


def headers(extra: dict | None = None) -> dict:
    h = {
        "User-Agent": ua(),
        "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "keep-alive",
    }
    if extra:
        h.update(extra)
    return h

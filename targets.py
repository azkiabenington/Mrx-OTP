#!/usr/bin/env python3
# targets.py - daftar endpoint OTP yang aktif (dicek 13-11-2026)
#
# key   : nama fungsi di handlers.py
# name  : label yang tampil di terminal
# via   : jalur pengiriman (WA / SMS)
# fmt   : format nomor yang dibutuhkan endpoint

TARGETS = [
    {"key": "tokopedia",            "name": "Tokopedia",                 "via": "WA",   "fmt": "08"},
    {"key": "tokopedia_sms",        "name": "Tokopedia SMS",             "via": "SMS",  "fmt": "08"},
    {"key": "bonusbelanja",         "name": "Bonus Belanja",             "via": "WA",   "fmt": "08"},
    {"key": "bonusbelanja_sms",     "name": "Bonus Belanja SMS",         "via": "SMS",  "fmt": "08"},
    {"key": "bonusbelanja_voice",   "name": "Bonus Belanja Voice Call",  "via": "CALL", "fmt": "08"},
    {"key": "kredione",             "name": "KrediOne",                  "via": "WA",   "fmt": "08"},
    {"key": "kredione_sms",         "name": "KrediOne SMS",              "via": "SMS",  "fmt": "08"},
    {"key": "kredione_voice",       "name": "KrediOne Voice Call",       "via": "CALL", "fmt": "08"},
    {"key": "duniagames",           "name": "Dunia Games",               "via": "SMS",  "fmt": "08"},
    {"key": "mapclub",              "name": "Mapclub",                   "via": "SMS",  "fmt": "08"},
    {"key": "cairin",               "name": "Cairin",                    "via": "SMS",  "fmt": "08"},
    {"key": "cairin_voice",          "name": "Cairin Voice Call",         "via": "CALL", "fmt": "08"},
    {"key": "indosaku",             "name": "Indosaku",                  "via": "SMS",  "fmt": "08"},
    {"key": "indosaku_voice",        "name": "Indosaku Voice Call",       "via": "CALL", "fmt": "08"},
    {"key": "indosaku_wa",           "name": "Indosaku WhatsApp",         "via": "WA",   "fmt": "08"},
    {"key": "kreditnavigator",      "name": "KreditNavigator",           "via": "SMS",  "fmt": "08"},
    {"key": "kreditnavigator_voice", "name": "KreditNavigator Voice Call", "via": "CALL", "fmt": "08"},
    {"key": "kreditnavigator_wa",    "name": "KreditNavigator WhatsApp", "via": "WA",   "fmt": "08"},
    {"key": "rupiahcepat",          "name": "RupiahCepat",               "via": "WA",   "fmt": "08"},
    {"key": "adakami",              "name": "AdaKami",                   "via": "AUTO", "fmt": "08"},
    {"key": "adiraku",              "name": "Adiraku",                   "via": "WA",   "fmt": "08"},
    {"key": "adiraku_sms",          "name": "Adiraku SMS",               "via": "SMS",  "fmt": "08"},
    {"key": "adiraku_voice",        "name": "Adiraku Voice Call",        "via": "CALL", "fmt": "08"},
    {"key": "singa",                "name": "Singa",                     "via": "WA",   "fmt": "08"},
    {"key": "singa_sms",            "name": "Singa SMS",                 "via": "SMS",  "fmt": "08"},
    {"key": "jogjakita",            "name": "JogjaKita",                 "via": "WA",   "fmt": "62"},
    {"key": "hrsbre",               "name": "HRS-BRE",                   "via": "WA",   "fmt": "08"},
    {"key": "redbus",               "name": "RedBus",                    "via": "SMS",  "fmt": "08"},
    {"key": "redbus_wa",             "name": "RedBus WhatsApp",           "via": "WA",   "fmt": "08"},
    {"key": "beautyhaul",           "name": "Beautyhaul",                "via": "WA",   "fmt": "08"},
    {"key": "beautyhaul_sms",        "name": "Beautyhaul SMS",            "via": "SMS",  "fmt": "08"},
    {"key": "beautyhaul_voice",      "name": "Beautyhaul Voice Call",     "via": "CALL", "fmt": "08"},
    {"key": "misteraladin",         "name": "Mister Aladin",             "via": "SMS",  "fmt": "08"},
    {"key": "cititrans_wa",         "name": "CitiTrans WhatsApp",        "via": "WA",   "fmt": "08"},
    {"key": "cititrans_sms",        "name": "CitiTrans SMS",             "via": "SMS",  "fmt": "08"},
    {"key": "soco",                 "name": "SOCO",                      "via": "WA",   "fmt": "08"},
    {"key": "soco_sms",             "name": "SOCO SMS",                  "via": "SMS",  "fmt": "08"},
    {"key": "paxbar",               "name": "Paxbar (agregator)",        "via": "AUTO", "fmt": "62"},
]

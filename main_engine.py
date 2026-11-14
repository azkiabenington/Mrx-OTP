#!/usr/bin/env python3
# main_engine.py - mesin pengiriman OTP
#
# Mengirim satu request per endpoint secara paralel lalu mengelompokkan hasilnya
# (SUCCESS / COOLDOWN / LIMITED / FAIL). Cooldown dan limit ditangani sebagai
# status normal, bukan error — sesuai perilaku situs asli.

import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from colorama import Fore, Style, init

from handlers import HANDLERS
from targets import TARGETS
from utils import fmt_08, fmt_plus, normalize

init(autoreset=True)

print_lock = threading.Lock()
file_lock = threading.Lock()
stop_flag = False
FAIL_LOG_FILE = "gagal_run.txt"


def record_failure(target: dict, status: str, detail: str, phone: str = ""):
    try:
        with file_lock:
            with open(FAIL_LOG_FILE, "a", encoding="utf-8") as f:
                ts = time.strftime("%Y-%m-%d %H:%M:%S")
                target_key = target.get("key", "-")
                target_name = target.get("name", "-")
                via = target.get("via", "-")
                f.write(f"[{ts}] {target_name} ({target_key}, {via}) -> {status}: {detail} | Target: {phone}\n")
    except Exception:
        pass


def _fmt(target: dict, n62: str) -> str:
    return fmt_plus(n62) if target["fmt"] == "plus" else fmt_08(n62) if target["fmt"] == "08" else n62


def log(idx, total, name, status, detail=""):
    with print_lock:
        if status == "SUCCESS":
            sym, col = "+", Fore.GREEN
        elif status in ("LIMITED", "COOLDOWN"):
            sym, col = "!", Fore.YELLOW
        elif status == "SKIP":
            sym, col = "-", Fore.MAGENTA
        else:
            sym, col = "x", Fore.RED
        line = f"{col}[{sym}]{Style.RESET_ALL} ({idx}/{total}) {name}: {status}"
        if detail:
            line += f" - {detail}"
        print(line, flush=True)


def process(target: dict, n62: str, idx: int, total: int) -> bool:
    if stop_flag:
        return False

    name = target["name"]
    fn = HANDLERS.get(target["key"])
    if fn is None:
        log(idx, total, name, "SKIP", "handler hilang")
        record_failure(target, "SKIP", "handler hilang", n62)
        return False

    n08 = fmt_08(n62)
    for attempt in range(2):
        try:
            ok, detail = fn(_fmt(target, n62), n62, n08)
        except Exception as exc:
            msg = type(exc).__name__
            if "Timeout" in msg:
                ok, detail = False, "timeout"
            elif "Connection" in msg or "MissingSchema" in msg:
                ok, detail = False, "koneksi gagal"
            elif "ModuleNotFoundError" in msg:
                ok, detail = False, "modul kurang"
            else:
                ok, detail = False, str(exc)[:40]
        low = (detail or "").lower()
        if not ok and "cooldown" in low:
            log(idx, total, name, "COOLDOWN", detail)
            return False
        if ok:
            log(idx, total, name, "SUCCESS", detail)
            return True
        if "limit" in low and attempt == 0:
            time.sleep(2)
            continue
        break

    log(idx, total, name, "FAIL", detail)
    record_failure(target, "FAIL", detail, n62)
    return False


def _run_all(n62: str, threads: int = 5) -> tuple[int, int]:
    total = len(TARGETS)
    success = 0
    with ThreadPoolExecutor(max_workers=max(1, threads)) as pool:
        futures = [pool.submit(process, t, n62, i, total) for i, t in enumerate(TARGETS, 1)]
        for f in as_completed(futures):
            if stop_flag:
                for x in futures:
                    x.cancel()
                break
            try:
                if f.result():
                    success += 1
            except Exception:
                pass
    return success, total


def _read_target(target: str | None) -> str | None:
    if not target:
        target = input(f"{Fore.WHITE}Nomor target (08xx / +62xx): {Style.RESET_ALL}").strip()
    if not target:
        print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Nomor kosong.")
        return None
    n62 = normalize(target)
    if not n62:
        print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Format nomor tidak valid. Contoh: 08123456789")
        return None
    return n62


def single_round(target: str | None = None, threads: int = 5) -> bool:
    global stop_flag
    stop_flag = False
    n62 = _read_target(target)
    if not n62:
        return False

    print()
    print(f"{Fore.CYAN}Target : {Fore.WHITE}+{n62}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Total  : {Fore.WHITE}{len(TARGETS)} endpoint{Style.RESET_ALL}")
    print()
    success, total = _run_all(n62, threads)
    print()
    print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Selesai. Sukses {success}/{total}")
    if success < total:
        print(f"{Fore.YELLOW}[INFO]{Style.RESET_ALL} Target gagal/skip dicatat di {FAIL_LOG_FILE}")
    if 0 < success < 3:
        print(f"{Fore.YELLOW}[WARN]{Style.RESET_ALL} Sukses sedikit, coba lagi beberapa saat lagi.")
    return success > 0


def infinite_loop(target: str | None = None, threads: int = 5, delay: int = 60) -> bool:
    global stop_flag
    stop_flag = False
    n62 = _read_target(target)
    if not n62:
        return False

    print()
    print(f"{Fore.CYAN}Target : {Fore.WHITE}+{n62}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Mode   : {Fore.WHITE}Infinite loop, jeda {delay}s{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}CTRL+C untuk berhenti.{Style.RESET_ALL}")
    print()

    total_ok = total_fail = rnd = 0
    try:
        while not stop_flag:
            rnd += 1
            print(f"{Fore.CYAN}[ROUND {rnd}]{Style.RESET_ALL} mulai...")
            ok, total = _run_all(n62, threads)
            total_ok += ok
            total_fail += total - ok
            print(f"{Fore.CYAN}[ROUND {rnd}]{Style.RESET_ALL} sukses {ok}/{total} "
                  f"| total sukses {total_ok} gagal {total_fail}")
            if stop_flag:
                break
            print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} jeda {delay} detik...\n")
            for _ in range(delay):
                if stop_flag:
                    break
                time.sleep(1)
    except KeyboardInterrupt:
        stop_flag = True
        print(f"\n{Fore.YELLOW}[WARN]{Style.RESET_ALL} dihentikan. total sukses {total_ok}, gagal {total_fail}")
    return total_ok > 0

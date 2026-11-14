#!/usr/bin/env python3
# main.py - Mrx-OTP v2
#
# Alat uji pengiriman OTP (OTP delivery tester) untuk nomor Indonesia.
# Murni memanggil endpoint publik yang sama dengan tombol "Kirim OTP" di situs resmi,
# jadi aman dipakai untuk QA / demo / skripsi tanpa akun atau API key pribadi.
# Tidak ada kode OTP yang ditebak — script hanya melaporkan apakah server menerima
# permintaan atau menolak karena limit/captcha.

import os
import sys
import time

from colorama import Fore, Style, init

from main_engine import infinite_loop, single_round
from targets import TARGETS

init(autoreset=True)

VERSION = "2.0"
BANNER = r"""
   __  _______  _  __        ____  ______ ____
  /  |/  / __ \| |/ /       / __ \/_  __/ __ \
 / /|_/ / /_/ /|   /  ____ / /_/ / / / / /_/ /
/_/  /_/_/ \_\/_/|_| /____/\____/ /_/ / ____/
                                     /_/
"""


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def ask_int(prompt: str, default: int, lo: int, hi: int) -> int:
    raw = input(f"{Fore.WHITE}{prompt} [{default}]: {Style.RESET_ALL}").strip()
    if not raw:
        return default
    try:
        val = int(raw)
    except ValueError:
        return default
    return max(lo, min(hi, val))


def banner():
    print(f"{Fore.GREEN}{BANNER}{Style.RESET_ALL}")
    print(f"  {Fore.WHITE}MRX-OTP {Fore.YELLOW}v{VERSION}{Style.RESET_ALL}  "
          f"{Fore.CYAN}|{Style.RESET_ALL} {len(TARGETS)} endpoint uji")
    print(f"  {Fore.CYAN}OTP delivery tester - tanpa login, tanpa data disimpan{Style.RESET_ALL}")
    print(f"  {Fore.CYAN}Untuk QA / demo / skripsi - {Fore.WHITE}MIT{Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}Dicek terakhir: 13 November 2026{Style.RESET_ALL}")
    print()


def menu():
    print(f"{Fore.WHITE}  [1]{Style.RESET_ALL} Single round  {Fore.CYAN}(kirim 1x ke semua endpoint){Style.RESET_ALL}")
    print(f"{Fore.WHITE}  [2]{Style.RESET_ALL} Infinite loop {Fore.CYAN}(ulang terus, jeda bisa diatur){Style.RESET_ALL}")
    print(f"{Fore.WHITE}  [3]{Style.RESET_ALL} Lihat daftar endpoint")
    print(f"{Fore.WHITE}  [4]{Style.RESET_ALL} Keluar")
    print()


def show_targets():
    print()
    print(f"{Fore.CYAN}Daftar endpoint ({len(TARGETS)}):{Style.RESET_ALL}")
    for i, t in enumerate(TARGETS, 1):
        print(f"  {i:2}. {t['name']:<22} {Fore.YELLOW}{t['via']}{Style.RESET_ALL}")
    print()
    print(f"{Fore.CYAN}Catatan:{Style.RESET_ALL} WA = WhatsApp, SMS = pesan biasa, CALL = panggilan suara, AUTO = bebas.")
    print("Kalau ada endpoint yang gagal terus, hapus barisnya di targets.py.")
    print()


def pause():
    input(f"\n{Fore.YELLOW}Enter untuk kembali...{Style.RESET_ALL}")


def main():
    while True:
        try:
            clear()
            banner()
            menu()
            choice = input(f"{Fore.WHITE}Pilih (1-4): {Style.RESET_ALL}").strip()

            if choice == "1":
                clear()
                banner()
                threads = ask_int("Jumlah thread", 5, 1, 15)
                print()
                try:
                    single_round(threads=threads)
                except KeyboardInterrupt:
                    print(f"\n{Fore.YELLOW}[WARN]{Style.RESET_ALL} dihentikan user")
                pause()

            elif choice == "2":
                clear()
                banner()
                threads = ask_int("Jumlah thread", 5, 1, 10)
                delay = ask_int("Jeda antar round (detik)", 60, 10, 600)
                print()
                infinite_loop(threads=threads, delay=delay)
                pause()

            elif choice == "3":
                clear()
                banner()
                show_targets()
                pause()

            elif choice == "4":
                print(f"\n{Fore.GREEN}Sampai jumpa.{Style.RESET_ALL}")
                return

        except KeyboardInterrupt:
            print(f"\n{Fore.GREEN}Sampai jumpa.{Style.RESET_ALL}")
            return
        except Exception as exc:
            print(f"\n{Fore.RED}[ERROR]{Style.RESET_ALL} {type(exc).__name__}: {exc}")
            if os.environ.get("MRX_DEBUG"):
                raise
            pause()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)

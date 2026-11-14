# MRX-OTP v2

Alat **uji pengiriman OTP** (OTP delivery tester) untuk nomor Indonesia. Cocok dipakai
untuk QA, demo, riset, dan pengecekan apakah SMS/WhatsApp OTP dari berbagai layanan
benar-benar sampai ke nomor tujuan.

Ini **bukan spam bot massal**, bukan bot login, dan bukan scraper data. Tidak butuh akun.
Script hanya melakukan apa yang dilakukan form "Kirim OTP" di situs resmi: mengirim satu
permintaan HTTP, lalu membaca jawaban server (berhasil / limit / captcha). Tidak ada kode
OTP yang ditebak atau diverifikasi di sini.


Endpoint lama banyak yang mati, jadi daftarnya diganti dengan endpoint yang masih hidup
dan sudah diuji. Status pengecekan terakhir: **13 November 2026**.

## Kenapa aman dipakai sebagai "tool testing"

- **Tanpa login & tanpa API key pribadi** — murni endpoint publik yang sama dengan yang
  dipanggil browser pengguna.
- **Read-only terhadap akun** — hanya meminta kode dikirim; tidak mengubah profil,
  saldo, atau transaksi.
- **Tidak menyimpan data** — nomor hanya dipakai selama proses berjalan, tidak ditulis
  ke file/database.
- **Tidak membanjiri** — satu putaran = satu request per layanan; layanan sendiri yang
  memasang cooldown (biasanya 60–180 detik per nomor).
- **Gratis dan open source** — bisa diaudit, di-rename, dan dimodifikasi bebas (MIT).

## Batasan yang wajar

- Ini **bukan** pengganti SMS gateway dan bukan alat DDoS. Trafiknya kecil dan sopan.
- Tiap layanan punya rate limit sendiri. Kalau kena `cooldown`, tunggu lalu coba lagi.
- Beberapa layanan membalas "sukses" walau operator menolak SMS-nya (nomor dianggap
  tidak valid). Karena itu selalu uji dengan nomor sendiri.
- Endpoint pihak ketiga bisa berubah sewaktu-waktu tanpa pemberitahuan.

## Endpoint

| # | Layanan | Jalur | Status uji |
|---|---------|-------|------------|
| 1 | Tokopedia | WhatsApp | `success: true` |
| 2 | Tokopedia SMS | SMS | `success: true` |
| 3 | Bonus Belanja | WhatsApp | `error: false` |
| 4 | Bonus Belanja SMS | SMS | `error: false` (`method: sms`) |
| 5 | Bonus Belanja Voice Call | Voice Call | `error: false` (`method: voice`) |
| 6 | KrediOne | WhatsApp | `suc: true` |
| 7 | KrediOne SMS | SMS | `suc: true` |
| 8 | KrediOne Voice Call | Voice Call | `suc: true` (`method: voice`) |
| 9 | Dunia Games | SMS | terkirim |
| 10 | Mapclub | SMS | `success: true` |
| 11 | Cairin | SMS | terkirim |
| 12 | Cairin Voice Call | Voice Call | `code: "0"` (`channel: voice`) |
| 13 | Indosaku | SMS | `code: 200` (channel 1 AES-ECB) |
| 14 | Indosaku Voice Call | Voice Call | `code: 200` (channel 2 AES-ECB) |
| 15 | Indosaku WhatsApp | WhatsApp | `code: 200` (channel 3 AES-ECB) |
| 16 | KreditNavigator | SMS | `lil: 0` (`xyldzdmx: TEXT`) |
| 17 | KreditNavigator Voice Call | Voice Call | `lil: 0` (`xyldzdmx: VOICE`) |
| 18 | KreditNavigator WhatsApp | WhatsApp | `lil: 0` (`xyldzdmx: WHATSAPP`) |
| 19 | RupiahCepat | WhatsApp | `code: 0` (`h5-whatsapp`) |
| 20 | AdaKami | OTP pinjol | slider otomatis, butuh `opencv` + `numpy` |
| 21 | Adiraku | WhatsApp | `messageIsSent: true` |
| 22 | Adiraku SMS | SMS | `messageIsSent: true` |
| 23 | Adiraku Voice Call | Voice Call | `messageIsSent: true` (`channel: voice`) |
| 24 | Singa | WhatsApp | `code: 200` |
| 25 | Singa SMS | SMS | `code: 200` (`sendCode`) |
| 26 | JogjaKita | WhatsApp | `rc: 200` (OAuth + OTP WA) |
| 27 | HRS-BRE | WhatsApp | `OTP Verification` |
| 28 | RedBus | SMS | `Code: 200` (SMS OTP) |
| 29 | RedBus WhatsApp | WhatsApp | `Code: 200` (`otpMode=WHATSAPP`) |
| 30 | Beautyhaul | WhatsApp | `HTTP 202` (save_register + send_otp) |
| 31 | Beautyhaul SMS | SMS | `HTTP 202` (`method: "SMS"`) |
| 32 | Beautyhaul Voice Call | Voice Call | `HTTP 202` (`method: "Voice"`) |
| 33 | Mister Aladin | SMS | `HTTP 200` / rate limit |
| 34 | CitiTrans WhatsApp | WhatsApp | `HTTP 200` (`method: "WHATSAPP"`) |
| 35 | CitiTrans SMS | SMS | `HTTP 200` (`method: "SMS"`) |
| 36 | SOCO | WhatsApp | `HTTP 200` (`mode: whatsapp`) |
| 37 | SOCO SMS | SMS | `HTTP 200` (`mode: sms`) |
| 38 | Paxbar | agregator | butuh kuota harian |

Ada yang pakai WhatsApp, SMS, dan Panggilan Suara (Voice Call). Kalau satu endpoint kena limit, endpoint lain
tetap jalan. Daftarnya ada di `targets.py`, tinggal hapus/tambah baris.

## Instalasi

Windows / Linux:

```bash
pip install -r requirements.txt
python main.py
```

Termux (Android):

```bash
pkg update && pkg upgrade
pkg install python git libjpeg-turbo libpng
pip install -r requirements.txt
python main.py
```

`opencv` di Termux sering gagal di-build. Kalau begitu, cukup `pip install requests colorama pycryptodome`
dan hapus baris `adakami` dari `targets.py`. Endpoint lain tetap jalan tanpa opencv.

## Cara pakai

1. Jalankan `python main.py`.
2. Pilih mode:
   - `1` single round: kirim sekali ke semua endpoint.
   - `2` infinite loop: ulang terus dengan jeda yang bisa diatur (default 60 detik).
   - `3` lihat daftar endpoint.
3. Masukkan nomor: `08xxxxxxxxxx`, `628xxxxxxxxxx`, atau `+628xxxxxxxxxx`.
4. `CTRL+C` untuk berhenti.

Contoh output:

```
[+] (1/13) Tokopedia: SUCCESS - OTP WhatsApp terkirim
[+] (11/13) Adiraku: SUCCESS - OTP WhatsApp terkirim
[x] (13/13) Paxbar (agregator): FAIL - Kuota API harian telah habis!
[INFO] Selesai. Sukses 12/13
```

## Untuk skripsi / demo / QA

Kalau kamu memakai ini untuk tugas akhir atau presentasi, framing yang aman dan jujur:

> Alat uji pengiriman OTP (bukan bot login) yang memanggil endpoint publik milik layanan
> Indonesia, lalu mengukur tingkat keberhasilan pengiriman SMS/WhatsApp OTP per layanan.

Yang bisa dilaporkan sebagai hasil uji: jumlah endpoint yang merespons, rasio berhasil
vs cooldown, dan jenis kanal (SMS/WhatsApp).

## Struktur file

| File | Isi |
|------|-----|
| `main.py` | menu & tampilan CLI |
| `main_engine.py` | mesin pengirim, thread pool, mode loop |
| `handlers.py` | request ke tiap endpoint + pengecekan respons |
| `targets.py` | daftar endpoint aktif |
| `utils.py` | normalisasi nomor |
| `useragents.py` | rotasi User-Agent |

## Catatan

- Endpoint pihak ketiga bisa berubah kapan saja. Kalau semua kena `rate limit`,
  tunggu 1-2 menit lalu coba lagi.
- `paxbar` pakai API key publik yang kuotanya terbatas. Bisa diganti lewat
  environment variable `PAXBAR_KEY`.
- Nomor dummy (`081234567890`) tetap dapat respons sukses walau OTP-nya tidak
  sampai, jadi selalu uji dengan nomor sendiri.
- Ini alat uji, bukan layanan resmi. Tidak ada jaminan OTP selalu sampai; hasil
  bergantung pada kebijakan operator dan layanan tujuan.

## Lisensi

MIT — lihat `LICENSE`. Bebas dipakai, diubah, dan di-rename, termasuk untuk tugas
kampus dan proyek pribadi. Atribusi tidak wajib tapi dihargai.

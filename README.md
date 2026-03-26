# Analisa Market — Forex Copilot Auto-Analysis

Repositori ini secara otomatis menganalisis data pasar XAUUSD dari file `forex_data.csv` menggunakan **GitHub Copilot Chat** setiap kali file tersebut diperbarui di branch `main`.

---

## Cara Kerja

1. **Trigger** — Workflow berjalan otomatis saat ada push ke `main` yang mengubah `forex_data.csv`.
2. **Analisa** — Seluruh isi `forex_data.csv` dikirim ke GitHub Copilot Chat API (`api.githubcopilot.com`). Copilot menganalisis data secara langsung tanpa indikator Python atau API AI eksternal.
3. **Output** — Copilot menghasilkan tepat **satu aksi trading** dalam format baku berikut:

   ```
   ⚡ XAUUSD — 26 Mar 2026, 12:01
   🔴 SELL @ 4425.87 SL 4445 | TP 4400
   Drop 100 poin dari 4520, pullback ke resistance 4425-4440. Lower high: 4520 → 4456 → 4432. Seller masih dominan.
   ```

   Atau untuk sinyal beli:

   ```
   ⚡ XAUUSD — 26 Mar 2026, 12:01
   🟢 BUY @ 4412.00 SL 4395 | TP 4440
   Breakout support 4400, momentum bullish. Higher low: 4380 → 4395 → 4412. Buyer masih dominan.
   ```

4. **Distribusi** — Hasil analisa dikirim ke:
   - Komentar pada commit yang memicu workflow (via GitHub REST API).
   - Pesan ke Telegram bot.

---

## Setup

### 1. Secrets yang Wajib Diset

Masuk ke **Settings → Secrets and variables → Actions → New repository secret** dan tambahkan:

| Secret Name | Keterangan |
|---|---|
| `COPILOT_TOKEN` | GitHub Personal Access Token (PAT) dengan scope `copilot`. Digunakan untuk mengakses GitHub Copilot Chat API. |
| `TELEGRAM_BOT_TOKEN` | Token bot Telegram yang diperoleh dari [@BotFather](https://t.me/BotFather). |
| `TELEGRAM_CHAT_ID` | ID chat/group Telegram tujuan pengiriman sinyal. |

> **Catatan:** `GITHUB_TOKEN` (untuk posting komentar commit) sudah tersedia secara otomatis oleh GitHub Actions — tidak perlu diset manual.

### 2. Cara Mendapatkan `COPILOT_TOKEN`

1. Buka <https://github.com/settings/tokens> → **Generate new token (classic)**.
2. Centang scope **`copilot`** (dan opsional `repo` jika perlu akses private).
3. Salin token, lalu simpan sebagai secret `COPILOT_TOKEN`.

### 3. Cara Mendapatkan `TELEGRAM_CHAT_ID`

Kirim pesan ke bot Anda, lalu akses:

```
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
```

Cari nilai `chat.id` dari pesan yang masuk.

---

## File Workflow

Workflow tersimpan di `.github/workflows/forex-copilot.yml`.

```
Trigger : push → main, paths: forex_data.csv
Job     : analyze (ubuntu-latest)
Steps   :
  1. checkout
  2. build Copilot prompt dari isi forex_data.csv
  3. POST ke https://api.githubcopilot.com/chat/completions
  4. POST komentar ke GitHub commit API
  5. POST pesan ke Telegram sendMessage API
```

---

## Format Output Baku

```
⚡ XAUUSD — DD MMM YYYY, HH:MM
🔴 SELL @ <harga_entry> SL <stop_loss> | TP <take_profit>
<Satu kalimat singkat alasan dalam Bahasa Indonesia, maks 25 kata.>
```

- Waktu menggunakan UTC 24 jam dalam format `DD MMM YYYY, HH:MM` (contoh: `26 Mar 2026, 12:01`).
- Hanya **satu baris aksi** (SELL atau BUY) dan **satu baris alasan**.
- Tidak ada teks tambahan di luar format ini.

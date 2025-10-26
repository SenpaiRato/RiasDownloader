<h1 align="center">🎵 Rias Khinsider Downloader</h1>

<p align="center">
 <img width="795" height="527" alt="image" src="https://github.com/user-attachments/assets/9855a852-9a66-410e-b587-6bea9ce711c6" />
</p>

<p align="center">
  <b>Download full game soundtracks from KHInsider with metadata, album art, and folder icons — all in one click.</b>
</p>

<p align="center">
  <a href="https://github.com/SenpaiRato/RiasKhinsiderDownloader/releases">
    <img src="https://img.shields.io/github/v/release/SenpaiRato/RiasKhinsiderDownloader?color=6aa6f8&style=for-the-badge" alt="Release">
  </a>
  <a href="https://github.com/SenpaiRato/RiasKhinsiderDownloader/issues">
    <img src="https://img.shields.io/github/issues/SenpaiRato/RiasKhinsiderDownloader?color=fcba03&style=for-the-badge" alt="Issues">
  </a>
  <a href="https://github.com/SenpaiRato/RiasKhinsiderDownloader/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/SenpaiRato/RiasKhinsiderDownloader?color=00c853&style=for-the-badge" alt="License">
  </a>
</p>

---

## ✨ Overview

**Rias Khinsider Downloader** is a modern, user-friendly desktop application built specifically to download **entire game soundtracks** from [KHInsider](https://downloads.khinsider.com).  
It preserves **track order**, embeds **metadata (ID3 tags)**, saves **album art**, and even **sets the folder icon** to match the album cover — all automatically.

> 💡 Built with ❤️ by [SenpaiRato](https://www.coffeebede.com/senpairato)

---

## 🚀 Features

| Feature | Description |
|--------|-------------|
| 🎵 **Full Album Download** | Download every track from a KHInsider album page in one go. |
| 🏷️ **Automatic Metadata** | Embeds album title, track title, and artist ("KHInsider") into MP3 files. |
| 🖼️ **Album Art as Folder Icon** | Sets the downloaded album cover as the Windows folder icon. |
| ⚡ **Parallel Downloads** | Uses multi-threading for fast, efficient downloads. |
| 🌓 **Dark/Light/System Theme** | Auto-saves your preferred UI theme between sessions. |
| 🧼 **No Python Required** | Standalone `.exe` — no runtime dependencies for end users. |
| 🛡️ **Privacy-Respecting** | No telemetry, no ads, no internet access beyond KHInsider. |

---

## 🧩 How to Use (For End Users)

> ✅ **You do NOT need Python installed if you use the pre-built executable!**

### ✳️ Step-by-step Setup

1. Go to the **[Releases page](https://github.com/SenpaiRato/RiasKhinsiderDownloader/releases)** and download the latest `.exe`.
2. Run the program.
3. Paste a KHInsider album URL (e.g., `https://downloads.khinsider.com/game-soundtracks/album/...`).
4. Choose a download folder.
5. Wait — Rias handles the rest! 🎶

> 🛑 **Note**: No cookies or login required! KHInsider is public and open.

---

## 🧰 For Developers (Running from Source)

If you want to run or modify the source code:

### Dependencies
```bash
pip install customtkinter yt-dlp beautifulsoup4 requests pillow tqdm mutagen

import sys
import os
import customtkinter as ctk
from tkinter import messagebox, filedialog
import threading
import re
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup, Tag, NavigableString
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image, ImageTk
import tkinter as tk
import ctypes
import webbrowser

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def sanitize_name(name: str) -> str:
    name = name.strip()
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    return name.strip()

thread_local = threading.local()

def get_session() -> requests.Session:
    if not hasattr(thread_local, "session"):
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        thread_local.session = session
    return thread_local.session

def get_album_tracks(album_url: str):
    session = get_session()
    try:
        response = session.get(album_url, timeout=15)
        response.raise_for_status()
    except:
        print("❌ Failed to load album page.")
        return None, [], None

    html = response.text
    if "Ooops! No such album" in html:
        print("❌ Album not found on KHInsider.")
        return None, [], None

    soup = BeautifulSoup(html, 'html.parser')
    title_tag = soup.select_one('#pageContent h2')
    album_title = sanitize_name(title_tag.get_text(strip=True)) if title_tag else "Untitled Album"

    album_image_url = None
    album_img_tag = soup.select_one('#pageContent .albumImage img')
    if album_img_tag and album_img_tag.get('src'):
        album_image_url = urljoin(album_url, album_img_tag['src'])

    table = soup.find('table', id='songlist')
    if not isinstance(table, Tag):
        print("❌ Could not find songlist table.")
        return album_title, [], album_image_url

    tracks = []
    for i, row in enumerate(table.find_all('tr')):
        if not isinstance(row, Tag) or row.get('id') in ['songlist_header', 'songlist_footer']:
            continue
        td = row.find('td', class_='clickable-row') or row.find('td', attrs={'colspan': True})
        if not isinstance(td, Tag): continue

        a_tag = td.find('a')
        if not isinstance(a_tag, Tag) or not a_tag.get('href'): continue
        
        title = a_tag.get_text(strip=True)
        if not title or title.strip().isdigit():
            title_parts = []
            for content in td.contents:
                if isinstance(content, NavigableString):
                    text = str(content).strip()
                    if text and not text.isdigit():
                        title_parts.append(text)
                elif isinstance(content, Tag) and content.name != 'a':
                    text = content.get_text(strip=True)
                    if text: title_parts.append(text)
            title = " ".join(title_parts).strip()

        page_url = urljoin(album_url, a_tag['href'])
        tracks.append({"title": sanitize_name(title) or f"Track {i+1}", "page_url": page_url})

    return album_title, tracks, album_image_url

def get_direct_download_link(song_page_url: str) -> str:
    session = get_session()
    try:
        response = session.get(song_page_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        btn = soup.find('a', id='downloadButton')
        if isinstance(btn, Tag) and btn.get('href'):
            href = btn['href']
            if isinstance(href, str) and href.endswith(('.mp3', '.flac')):
                return urljoin(song_page_url, href)

        audio = soup.find('audio', id='audio')
        if isinstance(audio, Tag) and audio.get('src'):
            src = audio['src']
            if isinstance(src, str):
                return urljoin(song_page_url, src)

        for a in soup.find_all('a', href=True):
            href = a['href']
            if isinstance(href, str) and href.endswith('.mp3'):
                return urljoin(song_page_url, href)
    except:
        pass
    return None

def download_song(song_url: str, folder_path: str, file_name: str):
    safe_name = sanitize_name(file_name) + ".mp3"
    file_path = os.path.join(folder_path, safe_name)
    if os.path.exists(file_path):
        return True, file_name

    session = get_session()
    try:
        response = session.get(song_url, stream=True, timeout=30)
        response.raise_for_status()
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(8192):
                f.write(chunk)
        return True, file_name
    except Exception as e:
        return False, f"{file_name}: Download failed"

def add_metadata_to_mp3(file_path, album_title, track_title):
    try:
        from mutagen.mp3 import MP3
        from mutagen.id3 import ID3, TIT2, TALB, TPE1
        audio = MP3(file_path, ID3=ID3)
        audio.tags.add(TIT2(encoding=3, text=track_title))
        audio.tags.add(TALB(encoding=3, text=album_title))
        audio.tags.add(TPE1(encoding=3, text="KHInsider"))
        audio.save()
    except ImportError:
        pass
    except:
        pass

def set_folder_icon(folder_path, image_path):
    try:
        from PIL import Image
        img = Image.open(image_path).convert("RGBA")
        img.thumbnail((256, 256), Image.Resampling.LANCZOS)
        png_path = os.path.join(folder_path, "album_icon.png")
        img.save(png_path, format='PNG')

        ini_path = os.path.join(folder_path, "desktop.ini")
        with open(ini_path, "w", encoding="utf-8") as f:
            f.write("[.ShellClassInfo]\n")
            f.write(f"IconResource={os.path.basename(png_path)},0\n")
            f.write("IconIndex=0\n")
            f.write("InfoTip=This is a music album folder.\n")
            f.write("ConfirmFileOp=0\n")
            f.write("Attributes=16\n")

        os.system(f'attrib +s "{folder_path}"')
        os.system(f'attrib +h "{ini_path}"')
        os.system(f'attrib +h "{png_path}"')

        SHChangeNotify = ctypes.windll.shell32.SHChangeNotify
        SHCNE_ASSOCCHANGED = 0x08000000
        SHCNF_IDLIST = 0x0000
        SHChangeNotify(SHCNE_ASSOCCHANGED, SHCNF_IDLIST, None, None)
    except:
        pass

class KHInsiderDownloaderUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Rias Khinsider Downloader")
        self.geometry("800x500")
        self.resizable(False, False)
        try:
            icon_path = resource_path("icon/icon.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception as e:
            print(f"Icon load error: {e}")

        self.load_settings()
        self.setup_ui()
        self.downloading = False
        self.current_album_image_path = None

    def load_settings(self):
        try:
            with open("settings.txt", "r", encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines:
                    if line.startswith("theme="):
                        saved_theme = line.split("=")[1].strip()
                        if saved_theme in ["Dark", "Light", "System"]:
                            ctk.set_appearance_mode(saved_theme)
                            break
                else:
                    ctk.set_appearance_mode("Dark")
        except FileNotFoundError:
            self.save_settings("Dark")
            ctk.set_appearance_mode("Dark")
        except:
            ctk.set_appearance_mode("Dark")

    def save_settings(self, theme):
        try:
            with open("settings.txt", "w", encoding='utf-8') as f:
                f.write(f"theme={theme}\n")
        except:
            pass

    def toggle_theme(self):
        current_mode = ctk.get_appearance_mode()
        if current_mode == "Dark":
            new_mode = "Light"
            self.mode_button.configure(text="☀️ Light Mode")
        elif current_mode == "Light":
            new_mode = "System"
            self.mode_button.configure(text="🌙 Dark Mode")
        else:
            new_mode = "Dark"
            self.mode_button.configure(text="🌙 Dark Mode")

        ctk.set_appearance_mode(new_mode)
        title_text_color = "white" if ctk.get_appearance_mode() == "Dark" else "black"
        if hasattr(self, 'title_label'):
            self.title_label.configure(text_color=title_text_color)

        self.save_settings(new_mode)

    def setup_ui(self):
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(pady=20, padx=40, fill="x")

        try:
            user_image_path = resource_path("icon/user_logo.png")
            if not os.path.exists(user_image_path):
                user_image_path = resource_path("icon/default_user.png")
            user_img = Image.open(user_image_path).resize((50, 50), Image.Resampling.LANCZOS)
            self.user_photo = ImageTk.PhotoImage(user_img)
            user_label = ctk.CTkLabel(header_frame, text="", image=self.user_photo, width=50, height=50)
            user_label.pack(side="left", padx=5)
        except:
            user_label = ctk.CTkLabel(header_frame, text="👤", font=ctk.CTkFont(size=20))
            user_label.pack(side="left", padx=5)

        title_text_color = "white" if ctk.get_appearance_mode() == "Dark" else "black"
        self.title_label = ctk.CTkLabel(
            header_frame,
            text="Rias is ready to serve",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=title_text_color
        )
        self.title_label.pack(side="left", padx=10)

        coffee_btn = ctk.CTkButton(
            header_frame,
            text="☕ Buy Me a Coffee",
            font=ctk.CTkFont(size=12, weight="bold"),
            width=200,
            height=40,
            command=self.open_coffee_site,
            fg_color="#FFA500",
            hover_color="#FF8C00",
            text_color="black"
        )
        coffee_btn.pack(side="left", padx=5)

        self.mode_button = ctk.CTkButton(
            header_frame,
            text="☀️ Light Mode" if ctk.get_appearance_mode().lower() == "dark" else "🌙 Dark Mode",
            width=120,
            font=ctk.CTkFont(size=10),
            command=self.toggle_theme
        )
        self.mode_button.pack(side="right")

        main_frame = ctk.CTkFrame(self)
        main_frame.pack(pady=5, padx=10, fill="both", expand=True)

        url_frame = ctk.CTkFrame(main_frame)
        url_frame.pack(pady=5, padx=10, fill="x")
        ctk.CTkLabel(url_frame, text="Album URL:").pack(anchor="w", padx=10, pady=(10,0))
        self.url_entry = ctk.CTkEntry(url_frame, placeholder_text="https://downloads.khinsider.com/game-soundtracks/...      ")
        self.url_entry.pack(fill="x", padx=10, pady=5)
        self.url_entry.bind('<Return>', lambda event: self.start_download())
        self.download_button = ctk.CTkButton(url_frame, text="Start Download", command=self.start_download)
        self.download_button.pack(pady=10)

        self.album_preview_frame = ctk.CTkFrame(main_frame)
        self.album_preview_frame.pack(pady=10, padx=10, fill="x")
        self.album_title_label = ctk.CTkLabel(self.album_preview_frame, text="No album loaded", font=ctk.CTkFont(size=16, weight="bold"))
        self.album_title_label.pack(pady=5)
        self.album_image_label = ctk.CTkLabel(self.album_preview_frame, text="No image")
        self.album_image_label.pack(pady=5)

        self.progress_bar = ctk.CTkProgressBar(main_frame)
        self.progress_bar.pack(pady=5, padx=20, fill="x")
        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(main_frame, text="Ready to download", font=ctk.CTkFont(size=12))
        self.status_label.pack(pady=5)

    def open_coffee_site(self):
        webbrowser.open("https://www.coffeebede.com/senpairato")

    def start_download(self):
        if self.downloading:
            return
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a URL")
            return

        parsed = urlparse(url)
        if parsed.netloc not in ("downloads.khinsider.com", "khinsider.com"):
            messagebox.showerror("Error", "Only https://downloads.khinsider.com URLs are supported.")
            return

        self.downloading = True
        self.download_button.configure(state="disabled", text="Downloading...")
        self.update_status("Fetching album information...")
        thread = threading.Thread(target=self.download_process, args=(url,))
        thread.daemon = True
        thread.start()

    def download_process(self, url):
        try:
            album_title, tracks, album_image_url = get_album_tracks(url)
            if not tracks:
                self.after(0, self.update_status, "❌ No tracks found or album is invalid.")
                self.after(0, self.reset_ui)
                return

            self.after(0, self.update_status, f"🎶 Album: {album_title}")
            self.after(0, self.update_status, f"🔢 Tracks: {len(tracks)}")
            self.after(0, self.update_album_preview, album_title, album_image_url)

            download_dir = filedialog.askdirectory(title="Select Download Directory")
            if not download_dir:
                self.after(0, self.update_status, "❌ No download directory selected.")
                self.after(0, self.reset_ui)
                return

            album_folder = os.path.join(download_dir, album_title)
            os.makedirs(album_folder, exist_ok=True)

            with open(os.path.join(album_folder, "info.txt"), "w", encoding="utf-8") as f:
                f.write(f"Album: {album_title}\nURL: {url}\nTracks: {len(tracks)}\nDownloaded: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

            self.after(0, self.update_status, "🔗 Fetching direct download links...")
            workers = min(5, os.cpu_count() or 4)
            direct_links = []
            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = [executor.submit(get_direct_download_link, track["page_url"]) for track in tracks]
                results = []
                for i, future in enumerate(as_completed(futures)):
                    results.append(future.result())
                    progress = (i + 1) / len(futures) * 0.3
                    self.after(0, self.update_progress, progress, f"Getting links... {i+1}/{len(futures)}")

                for i, dl_url in enumerate(results):
                    if dl_url:
                        direct_links.append({"title": tracks[i]["title"], "direct_url": dl_url})

            if not direct_links:
                self.after(0, self.update_status, "❌ No valid download links found!")
                self.after(0, self.reset_ui)
                return

            self.after(0, self.update_status, f"🚀 Downloading {len(direct_links)} files...")
            tasks = [(item["direct_url"], album_folder, f"{i+1:03d} - {item['title']}") for i, item in enumerate(direct_links)]
            failed = []
            dl_workers = min(6, len(tasks))
            with ThreadPoolExecutor(max_workers=dl_workers) as dl_executor:
                futures = [dl_executor.submit(download_song, *task) for task in tasks]
                completed = 0
                for future in as_completed(futures):
                    success, msg = future.result()
                    completed += 1
                    progress = 0.3 + (completed / len(futures)) * 0.7
                    self.after(0, self.update_progress, progress, f"Downloading... {completed}/{len(futures)}")
                    if success:
                        file_name = msg
                        file_path = os.path.join(album_folder, sanitize_name(file_name) + ".mp3")
                        add_metadata_to_mp3(file_path, album_title, file_name)
                    else:
                        failed.append(msg)

            if failed:
                self.after(0, self.update_status, f"⚠️ {len(failed)} download(s) failed.")
            else:
                self.after(0, self.update_status, "🎉 All downloads completed successfully!")

            if album_image_url:
                self.after(0, self.update_status, "🖼️ Downloading album image for folder icon...")
                try:
                    from PIL import Image
                    import requests
                    from io import BytesIO
                    response = requests.get(album_image_url)
                    img_data = BytesIO(response.content)
                    img = Image.open(img_data).convert("RGBA")
                    img.thumbnail((256, 256), Image.Resampling.LANCZOS)
                    img_path = os.path.join(album_folder, "album_icon.png")
                    img.save(img_path, format='PNG')
                    self.current_album_image_path = img_path
                    self.after(0, self.update_status, "✅ Album image downloaded and saved as PNG.")
                except Exception as e:
                    self.after(0, self.update_status, f"⚠️ Could not download album image: {str(e)}")
                    self.current_album_image_path = None

            if self.current_album_image_path:
                self.after(0, self.update_status, "🎨 Setting folder icon...")
                set_folder_icon(album_folder, self.current_album_image_path)

            if failed:
                self.after(0, self.update_status, f"📁 Files saved to: {os.path.abspath(album_folder)} | {len(failed)} failed")
            else:
                self.after(0, self.update_status, f"📁 Files saved to: {os.path.abspath(album_folder)}")

            self.after(0, self.show_notification, album_title, len(direct_links), len(failed))

        except Exception as e:
            self.after(0, self.update_status, f"❌ Error during download: {str(e)}")
        finally:
            self.after(0, self.reset_ui)

    def update_album_preview(self, title, image_url):
        self.album_title_label.configure(text=title)
        if image_url:
            try:
                from PIL import Image, ImageTk
                import requests
                from io import BytesIO
                response = requests.get(image_url)
                img_data = BytesIO(response.content)
                img = Image.open(img_data).resize((150, 150), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.album_image_label.configure(image=photo, text="")
                self.album_image_label.image = photo
            except:
                self.album_image_label.configure(text="Could not load image", image=None)
        else:
            self.album_image_label.configure(text="No image available", image=None)

    def show_notification(self, album_title, total_tracks, failed_count):
        if failed_count == 0:
            msg = f"Downloaded {total_tracks} tracks from '{album_title}'!"
        else:
            msg = f"Downloaded {total_tracks - failed_count} of {total_tracks} tracks from '{album_title}'. {failed_count} failed."
        messagebox.showinfo("Download Complete", msg)

    def update_progress(self, value, text):
        self.progress_bar.set(value)
        self.status_label.configure(text=text)

    def update_status(self, text):
        self.status_label.configure(text=text)

    def reset_ui(self):
        self.downloading = False
        self.download_button.configure(state="normal", text="Start Download")
        self.progress_bar.set(0)
        self.status_label.configure(text="Ready to download")

if __name__ == "__main__":
    app = KHInsiderDownloaderUI()
    app.mainloop()

import instaloader
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import os
from datetime import datetime

def setup_instagram():
    """Настройка и авторизация в Instagram"""
    try:
        L = instaloader.Instaloader(
            download_videos=True,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False
        )
        return L
    except Exception as e:
        print(f"Ошибка при настройке Instagram: {e}")
        return None

def setup_google_drive():
    """Настройка и авторизация в Google Drive"""
    try:
        gauth = GoogleAuth()
        # Используем существующие настройки из settings.yaml
        gauth.LocalWebserverAuth()
        drive = GoogleDrive(gauth)
        return drive
    except Exception as e:
        print(f"Ошибка при настройке Google Drive: {e}")
        return None

def download_reels(username, L):
    """Скачивание рилсов"""
    try:
        if not os.path.exists("downloads"):
            os.makedirs("downloads")
        
        profile = instaloader.Profile.from_username(L.context, username)
        print(f"Начинаю скачивание рилсов пользователя {username}")
        
        for post in profile.get_posts():
            if post.is_video:
                print(f"Скачиваю рилс: {post.date}")
                L.download_post(post, target="downloads")
        return True
    except Exception as e:
        print(f"Ошибка при скачивании: {e}")
        return False

def upload_to_drive(drive):
    """Загрузка файлов на Google Drive"""
    try:
        folder_name = f"Instagram_Reels_{datetime.now().strftime('%Y-%m-%d')}"
        folder_metadata = {
            'title': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = drive.CreateFile(folder_metadata)
        folder.Upload()
        
        for filename in os.listdir("downloads"):
            if filename.endswith(".mp4"):
                file_path = os.path.join("downloads", filename)
                file = drive.CreateFile({
                    'title': filename,
                    'parents': [{'id': folder['id']}]
                })
                file.SetContentFile(file_path)
                print(f"Загружаю файл: {filename}")
                file.Upload()
        return True
    except Exception as e:
        print(f"Ошибка при загрузке на Google Drive: {e}")
        return False

def main():
    # Инициализация Instagram
    L = setup_instagram()
    if not L:
        return
    
    # Инициализация Google Drive
    drive = setup_google_drive()
    if not drive:
        return
    
    # Замените на нужный username
    target_username = "kekzik"
    
    # Скачивание и загрузка
    if download_reels(target_username, L):
        if upload_to_drive(drive):
            print("Процесс успешно завершен!")
        else:
            print("Ошибка при загрузке на Google Drive")
    else:
        print("Ошибка при скачивании рилсов")

if __name__ == "__main__":
    main() 
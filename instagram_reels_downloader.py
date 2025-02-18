import os
import time
from datetime import datetime
import instaloader
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from config import (
    INSTAGRAM_CONFIG,
    GDRIVE_CONFIG,
    DOWNLOAD_CONFIG,
    INSTALOADER_CONFIG
)
import logging
import socks
import socket

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('instagram_downloader.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ReelsDownloader:
    def __init__(self):
        logger.info("Инициализация ReelsDownloader")
        try:
            # Настройка прокси если он включен
            if INSTAGRAM_CONFIG['proxy']['use_proxy']:
                self._setup_proxy()
            
            # Инициализация Instagram
            logger.info("Создание экземпляра Instaloader")
            self.insta = instaloader.Instaloader(**INSTALOADER_CONFIG)
            
            # Создание папки для временного хранения
            self.temp_folder = DOWNLOAD_CONFIG['temp_folder']
            logger.info(f"Проверка/создание временной папки: {self.temp_folder}")
            if not os.path.exists(self.temp_folder):
                os.makedirs(self.temp_folder)
                logger.info("Временная папка создана")
            
            # Инициализация Google Drive
            logger.info("Инициализация подключения к Google Drive")
            self.drive = self._init_google_drive()
            
            # Список целевых аккаунтов
            self.target_accounts = INSTAGRAM_CONFIG['target_accounts']
            logger.info(f"Целевые аккаунты: {self.target_accounts}")
        except Exception as e:
            logger.error(f"Ошибка при инициализации: {str(e)}", exc_info=True)
            raise

    def _setup_proxy(self):
        """Настройка прокси для всех соединений"""
        logger.info("Настройка прокси")
        proxy_config = INSTAGRAM_CONFIG['proxy']
        
        # Определяем тип прокси
        proxy_type = {
            'http': socks.HTTP,
            'socks4': socks.SOCKS4,
            'socks5': socks.SOCKS5
        }.get(proxy_config['proxy_type'])
        
        if proxy_type:
            # Устанавливаем прокси глобально
            socks.set_default_proxy(
                proxy_type,
                proxy_config['host'],
                proxy_config['port'],
                username=proxy_config['username'],
                password=proxy_config['password']
            )
            socket.socket = socks.socksocket
            logger.info(f"Прокси настроен: {proxy_config['host']}:{proxy_config['port']}")

    def _init_google_drive(self):
        logger.info("Начало инициализации Google Drive")
        try:
            gauth = GoogleAuth()
            logger.info("Попытка загрузки сохраненных учетных данных")
            gauth.LoadCredentialsFile(GDRIVE_CONFIG['credentials_file'])
            
            if gauth.credentials is None:
                logger.info("Учетные данные отсутствуют, запуск локальной авторизации")
                gauth.LocalWebserverAuth()
            elif gauth.access_token_expired:
                logger.info("Токен доступа истек, обновление")
                gauth.Refresh()
            else:
                logger.info("Авторизация с существующими учетными данными")
                gauth.Authorize()
                
            logger.info("Сохранение учетных данных")
            gauth.SaveCredentialsFile(GDRIVE_CONFIG['credentials_file'])
            return GoogleDrive(gauth)
        except Exception as e:
            logger.error(f"Ошибка при инициализации Google Drive: {str(e)}", exc_info=True)
            raise

    def login_to_instagram(self):
        logger.info("Попытка входа в Instagram")
        try:
            self.insta.login(
                INSTAGRAM_CONFIG['username'],
                INSTAGRAM_CONFIG['password']
            )
            logger.info("Успешный вход в Instagram")
            return True
        except Exception as e:
            logger.error(f"Ошибка входа в Instagram: {str(e)}", exc_info=True)
            return False

    def download_reels(self):
        logger.info("Начало процесса загрузки рилсов")
        for account in self.target_accounts:
            try:
                logger.info(f"Обработка аккаунта: {account}")
                profile = instaloader.Profile.from_username(self.insta.context, account)
                logger.info(f"Профиль получен: {account}")
                
                # Получаем последние посты
                logger.info(f"Получение последних {INSTAGRAM_CONFIG['posts_limit']} постов")
                posts = list(profile.get_posts())[:INSTAGRAM_CONFIG['posts_limit']]
                logger.info(f"Получено постов: {len(posts)}")
                
                for post in posts:
                    if post.is_video and not self._is_already_downloaded(post.shortcode):
                        try:
                            logger.info(f"Загрузка рилса: {post.shortcode}")
                            self.insta.download_post(post, target=self.temp_folder)
                            logger.info(f"Рилс загружен: {post.shortcode}")
                            
                            self._upload_to_drive(post.shortcode)
                            
                            logger.info(f"Пауза {INSTAGRAM_CONFIG['download_delay']} секунд")
                            time.sleep(INSTAGRAM_CONFIG['download_delay'])
                        except Exception as e:
                            logger.error(f"Ошибка при загрузке рилса {post.shortcode}: {str(e)}", exc_info=True)
                
            except Exception as e:
                logger.error(f"Ошибка при обработке аккаунта {account}: {str(e)}", exc_info=True)
                continue

    def _is_already_downloaded(self, shortcode):
        try:
            logger.info(f"Проверка наличия рилса {shortcode} на Google Drive")
            folder_id = self._get_or_create_folder(GDRIVE_CONFIG['folder_name'])
            file_list = self.drive.ListFile({'q': f"'{folder_id}' in parents"}).GetList()
            return any(shortcode in file['title'] for file in file_list)
        except Exception as e:
            logger.error(f"Ошибка при проверке наличия рилса: {str(e)}", exc_info=True)
            return False

    def _get_or_create_folder(self, folder_name):
        logger.info(f"Получение/создание папки: {folder_name}")
        try:
            folders = self.drive.ListFile({
                'q': f"title='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            }).GetList()
            
            if folders:
                logger.info(f"Папка найдена: {folder_name}")
                return folders[0]['id']
            else:
                logger.info(f"Создание новой папки: {folder_name}")
                folder = self.drive.CreateFile({
                    'title': folder_name,
                    'mimeType': 'application/vnd.google-apps.folder'
                })
                folder.Upload()
                return folder['id']
        except Exception as e:
            logger.error(f"Ошибка при работе с папкой: {str(e)}", exc_info=True)
            raise

    def _upload_to_drive(self, shortcode):
        logger.info(f"Начало загрузки рилса {shortcode} на Google Drive")
        folder_id = self._get_or_create_folder(GDRIVE_CONFIG['folder_name'])
        
        try:
            for filename in os.listdir(self.temp_folder):
                if shortcode in filename and filename.endswith(DOWNLOAD_CONFIG['video_format']):
                    file_path = os.path.join(self.temp_folder, filename)
                    logger.info(f"Найден файл для загрузки: {file_path}")
                    
                    file_drive = self.drive.CreateFile({
                        'title': f"reel_{shortcode}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{DOWNLOAD_CONFIG['video_format']}",
                        'parents': [{'id': folder_id}]
                    })
                    file_drive.SetContentFile(file_path)
                    logger.info("Загрузка файла на Google Drive")
                    file_drive.Upload()
                    
                    logger.info(f"Удаление временного файла: {file_path}")
                    os.remove(file_path)
                    logger.info(f"Рилс {shortcode} успешно загружен на Google Drive")
                    break
        except Exception as e:
            logger.error(f"Ошибка при загрузке на Google Drive: {str(e)}", exc_info=True)

    def cleanup(self):
        logger.info("Начало очистки временных файлов")
        for filename in os.listdir(self.temp_folder):
            file_path = os.path.join(self.temp_folder, filename)
            try:
                if os.path.isfile(file_path):
                    logger.info(f"Удаление файла: {file_path}")
                    os.remove(file_path)
            except Exception as e:
                logger.error(f"Ошибка при удалении файла {file_path}: {str(e)}", exc_info=True)

def main():
    logger.info("Запуск программы")
    try:
        downloader = ReelsDownloader()
        
        if downloader.login_to_instagram():
            try:
                downloader.download_reels()
            except Exception as e:
                logger.error(f"Ошибка при загрузке рилсов: {str(e)}", exc_info=True)
            finally:
                logger.info("Запуск очистки")
                downloader.cleanup()
        else:
            logger.error("Не удалось войти в Instagram")
    except Exception as e:
        logger.error(f"Критическая ошибка: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main() 
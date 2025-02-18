# Instagram настройки
INSTAGRAM_CONFIG = {
    'username': 'igtestai',
    'password': '403012qW',
    'target_accounts': [
        'kekzik',
        'dioooon'
    ],
    'posts_limit': 10,  # Количество последних постов для проверки
    'download_delay': 2,  # Задержка между загрузками в секундах
}

# Google Drive настройки
GDRIVE_CONFIG = {
    'credentials_file': 'mycreds.txt',
    'folder_name': 'Instagram Reels'
}

# Настройки загрузки
DOWNLOAD_CONFIG = {
    'temp_folder': 'temp_reels',
    'video_format': '.mp4'
}

# Настройки Instaloader
INSTALOADER_CONFIG = {
    'download_videos': True,
    'download_video_thumbnails': False,
    'download_geotags': False,
    'download_comments': False,
    'save_metadata': False
} 
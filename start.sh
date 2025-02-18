#!/bin/bash
# Установка зависимостей
pip install -r requirements.txt

# Создание необходимых директорий
mkdir -p temp_reels

# Запуск приложения
python instagram_reels_downloader.py 
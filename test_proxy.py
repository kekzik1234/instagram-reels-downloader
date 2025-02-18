import requests
import logging
from datetime import datetime
import socket
import socks

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_proxy(proxy_host, proxy_port, proxy_type='http', username=None, password=None):
    try:
        logger.info(f"Тестирование прокси {proxy_type}://{proxy_host}:{proxy_port}")
        
        auth_string = f"{username}:{password}@" if username and password else ""
        
        if proxy_type.startswith('socks'):
            # Настройка SOCKS прокси
            socks_type = socks.SOCKS5 if proxy_type == 'socks5' else socks.SOCKS4
            socks.set_default_proxy(
                socks_type, 
                proxy_host, 
                int(proxy_port),
                username=username,
                password=password
            )
            socket.socket = socks.socksocket
            
            # Тестируем соединение
            response = requests.get('https://www.instagram.com', timeout=10)
        else:
            # Настройка HTTP/HTTPS прокси
            proxy_url = f"{proxy_type}://{auth_string}{proxy_host}:{proxy_port}"
            proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
            response = requests.get('https://www.instagram.com', proxies=proxies, timeout=10)
        
        logger.info(f"Статус: {response.status_code}")
        return True
    except Exception as e:
        logger.error(f"Ошибка: {str(e)}")
        return False
    finally:
        # Сбрасываем настройки сокета
        if proxy_type.startswith('socks'):
            socket.socket = socket.socket

# Список прокси для тестирования
proxies_to_test = [
    # HTTP/HTTPS прокси
    {'host': '91.241.217.58', 'port': '9812', 'type': 'http'},
    {'host': '45.142.106.202', 'port': '8094', 'type': 'http'},
    {'host': '45.142.106.7', 'port': '8094', 'type': 'http'},
    # SOCKS5 прокси
    {'host': '184.178.172.18', 'port': '15280', 'type': 'socks5'},
    {'host': '72.210.252.134', 'port': '4145', 'type': 'socks5'},
    {'host': '98.188.47.132', 'port': '4145', 'type': 'socks5'},
    {'host': '184.178.172.28', 'port': '15294', 'type': 'socks5'},
    {'host': '142.54.226.214', 'port': '4145', 'type': 'socks5'},
    # Дополнительные прокси с аутентификацией
    {
        'host': 'proxy.webshare.io', 
        'port': '80', 
        'type': 'http',
        'username': 'xpwrxsiy-rotate',
        'password': 'tl4i2oqxqehs'
    },
]

found_working_proxy = False
for proxy in proxies_to_test:
    if test_proxy(
        proxy['host'], 
        proxy['port'], 
        proxy['type'],
        proxy.get('username'),
        proxy.get('password')
    ):
        print(f"Найден рабочий прокси: {proxy['type']}://{proxy['host']}:{proxy['port']}")
        found_working_proxy = True
        break

if not found_working_proxy:
    print("Не найдено рабочих прокси") 
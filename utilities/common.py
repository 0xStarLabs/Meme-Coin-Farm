import random
import requests


def read_files():
    with open("./data/private_keys.txt") as file:
        private_keys = [line.strip() for line in file if line.strip()]

    with open("./data/proxies.txt") as file:
        proxies = [line.strip() for line in file if line.strip()]

    while len(proxies) < len(private_keys):
        proxies.append(random.choice(proxies))

    return private_keys, proxies

def create_client(proxy: str) -> requests.Session:
    session = requests.Session()

    if proxy:
        session.proxies.update({
            "http": "http://" + proxy,
            "https": "http://" + proxy,
        })

    session.headers.update({
        'authority': 'memefarm-api.memecoin.org',
        'accept': 'application/json',
        'accept-language': 'uk',
        'origin': 'https://www.memecoin.org',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })

    return session
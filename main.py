import sys
import urllib3
import random
import time
import functools
import requests
from eth_account import Account
from loguru import logger
from eth_account.messages import encode_defunct
from concurrent.futures import ThreadPoolExecutor
import threading


lock = threading.Lock()
private_keys_with_points = []

def retry(max_attempts=5):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    if attempts >= max_attempts:
                        raise
                    time.sleep(5) 
            return None
        return wrapper
    return decorator


@retry()
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
        'sec-ch-ua': '"Google Chrome";v="110", "Chromium";v="110", "Not=A?Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
    })

    return session


@retry()
def login(wallet, client):
    try:
        message = f'The wallet will be used for MEME allocation. If you referred friends, family, lovers or strangers, ensure this wallet has the NFT you referred.\n\nBut also...\n\nNever gonna give you up\nNever gonna let you down\nNever gonna run around and desert you\nNever gonna make you cry\nNever gonna say goodbye\nNever gonna tell a lie and hurt you\n\nWallet: {wallet.address[:5]}...{wallet.address[-4:]}'
        message_encode = encode_defunct(text=message)
        signed_message = wallet.sign_message(message_encode)
        signature = signed_message["signature"].hex()
        json_data = {
            'address': wallet.address,
            'delegate': wallet.address,
            'message': message,
            'signature': signature,
        }

        response = client.post('https://memefarm-api.memecoin.org/user/wallet-auth', json=json_data)
        response_data = response.json()
        
        if 'status' in response_data and response_data['status'] == 401:
            logger.info(f"Wallet: {wallet.address} has no points")
            return None

        access_token = response_data['accessToken']
        return access_token
    except Exception as e:
        logger.error(f"Error in login: {e}")
        return None



@retry()
def get_points(client, access_token):
    try:
        client.headers["authorization"] = f"Bearer {access_token}"
        response = client.get('https://memefarm-api.memecoin.org/user/tasks')
        response_data = response.json()
        current_points = response_data['points']['current']
        return current_points
    except Exception as e:
        logger.error(f"Error in get_points: {e}")
        None
    

@retry()
def check(private_key: str, proxy: str):
    try:
        wallet = Account.from_key(private_key)
        client = create_client(proxy)
        access_token = login(wallet, client)
        
        if access_token:
            points = get_points(client, access_token)
            if points and points > 0:
                logger.success(f"Wallet {wallet.address} has {points} points")
                with lock:
                    private_keys_with_points.append(private_key)
    except Exception as e:
        logger.error(f"Error in check: {e}")
        None


def save_private_keys():
    unique_private_keys = list(set(key.strip() for key in private_keys_with_points))
    with open("private_keys_with_points.txt", "w") as file:
        for key in unique_private_keys:
            file.write(key + "\n")

def configuration():
    urllib3.disable_warnings()
    logger.remove()
    logger.add(sys.stdout, colorize=True,
               format="<light-cyan>{time:HH:mm:ss}</light-cyan> | <level> {level: <8}</level> | - <white>{"
                      "message}</white>")

def main():
    configuration()
    with open("./private_keys.txt") as file:
        private_keys = [line.strip() for line in file if line.strip()]

    with open("./proxies.txt") as file:
        proxies = [line.strip() for line in file if line.strip()]

    while len(proxies) < len(private_keys):
        proxies.append(random.choice(proxies))

    num_threads = int(input("Enter the number of threads: "))
    
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        for private_key, proxy in zip(private_keys, proxies):
            executor.submit(check, private_key, proxy)

    save_private_keys()

main()

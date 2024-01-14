import threading
from eth_account.messages import encode_defunct
from loguru import logger
from eth_account import Account
from utilities.common import create_client


lock = threading.Lock()
private_keys = []
proxies = []


def save_private_keys_and_proxies():
        unique_private_keys = list(set(key.strip() for key in private_keys))
        unique_proxies = list(set(proxy.strip() for proxy in proxies))

        with open("./data/private_keys_with_points.txt", "w") as file:
            for key in unique_private_keys:
                file.write(key + "\n")
        with open("./data/proxies_with_points.txt", "w") as file:
            for proxy in unique_proxies:
                file.write(proxy + "\n")


class Checker():
    def __init__(self, private_key, proxy) -> None:
        self.private_key = private_key
        self.wallet = Account.from_key(private_key)
        self.proxy = proxy
        self.client = create_client(proxy)


    def login(self):
        try:
            message = f'The wallet will be used for MEME allocation. If you referred friends, family, lovers or strangers, ensure this wallet has the NFT you referred.\n\nBut also...\n\nNever gonna give you up\nNever gonna let you down\nNever gonna run around and desert you\nNever gonna make you cry\nNever gonna say goodbye\nNever gonna tell a lie and hurt you\n\nWallet: {self.wallet.address[:5]}...{self.wallet.address[-4:]}'
            message_encode = encode_defunct(text=message)
            signed_message = self.wallet.sign_message(message_encode)
            signature = signed_message["signature"].hex()
            json_data = {
                'address': self.wallet.address,
                'delegate': self.wallet.address,
                'message': message,
                'signature': signature,
            }
            
            response = self.client.post('https://memefarm-api.memecoin.org/user/wallet-auth', json=json_data)
            response_data = response.json()
            if 'error' in response_data:
                logger.info(f"Wallet: {self.wallet.address} has no points")
                return None
            
            access_token = response_data['accessToken']
            return access_token
        except Exception as e:
            logger.error(f"Error in login: {e}")
            return None


    def get_points(self, access_token):
        try:
            self.client.headers["authorization"] = f"Bearer {access_token}"
            response = self.client.get('https://memefarm-api.memecoin.org/user/tasks')
            response_data = response.json()
            current_points = response_data['points']['current']
            return current_points
        except Exception as e:
            logger.error(f"Error in get_points: {e}")
            None

    def check(self):
        try:
            access_token = self.login()
            
            if access_token:
                points = self.get_points(access_token)
                if points and points > 0:
                    logger.success(f"Wallet {self.wallet.address} has {points} points")
                    with lock:
                        private_keys.append(self.private_key)
                        proxies.append(self.proxy)
        except Exception as e:
            logger.error(f"Error in check: {e}")
            None

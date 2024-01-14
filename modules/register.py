import time
import threading
from eth_account.messages import encode_defunct
from loguru import logger
from eth_account import Account
from utilities.common import create_client
from modules.hcaptcha import HCaptchaSolver
from modules.recaptcha import ReCaptchaSolver


lock = threading.Lock()
private_keys = []
proxies = []


def save_private_keys_and_proxies():
        unique_private_keys = list(set(key.strip() for key in private_keys))
        unique_proxies = list(set(proxy.strip() for proxy in proxies))

        with open("./data/private_keys_registered.txt", "w") as file:
            for key in unique_private_keys:
                file.write(key + "\n")
        with open("./data/proxies_registered.txt", "w") as file:
            for proxy in unique_proxies:
                file.write(proxy + "\n")

class Register():
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

    def recaptcha_solver(self) -> None:
        recaptcha = ReCaptchaSolver(self.wallet, self.client)
        response: None = None
        
        while True:
            try:
                recaptcha_token: str = recaptcha.recaptcha_solver()

                response = self.client.post(
                    url='https://memefarm-api.memecoin.org/user/verify/recaptcha',
                    json={
                        'code': recaptcha_token
                    })

                if response.json()['status'] == 'success':
                    logger.success(f'{self.wallet.address} | Seccussfully solved reCaptcha')
                    return

                logger.error(f'{self.wallet.address} | reCaptcha: {response.text()}')
                time.sleep(5)
                
            except Exception as error:
                if response:
                    logger.error(f'{self.wallet.address} | Google reCaptcha: {error}, {self.wallet.address}')
                    time.sleep(5)

                else:
                    logger.error(f'{self.wallet.address} | Google reCaptcha: {error}')
                    time.sleep(5)

    def hcaptcha_solver(self) -> None:
        hcaptcha = HCaptchaSolver(self.wallet, self.client)
        response: None = None

        while True:
            try:
                captcha_response, user_agent = hcaptcha.hcaptcha_solver()
                
                self.client.headers['user-agent']: str = user_agent

                response = self.client.post(
                    url='https://memefarm-api.memecoin.org/user/verify/hcaptcha',
                    json={
                        'code': captcha_response
                    })

                if response.json()['status'] == 'success':
                    logger.success(f'{self.wallet.address} | Seccussfully solved hCaptcha')
                    return

                logger.error(f'{self.wallet.address} | hCaptcha: {response.text()}')
                time.sleep(5)

            except Exception as error:
                if response:
                    logger.error(f'{self.wallet.address} reCaptcha: {response.text()}')
                    time.sleep(5)
                else:
                    logger.error(f'{self.wallet.address} | reCaptcha: {error}')
                    time.sleep(5)
                        
    def register(self):
        self.recaptcha_solver()
        self.hcaptcha_solver()
        
        while True:
            try:
                response = self.client.post(
                    url='https://memefarm-api.memecoin.org/user/verify/wallet-balance',
                    json=False)

                return response.json()['status'] == 'success'

            except Exception as error:
                if response:
                    logger.error(f'{self.wallet.address}: {response.text()}')
                    time.sleep(5)
                else:
                    logger.error(f'{self.wallet.address}: {error}')
                    time.sleep(5)

    def execute(self):
        try:
            access_token = self.login()
            if access_token:
                self.client.headers["authorization"] = f"Bearer {access_token}"
                response = self.register()
                if response:
                    logger.success(f"Wallet {self.wallet.address} successfully registered")
                    with lock:
                        private_keys.append(self.private_key)
                        proxies.append(self.proxy)

        except Exception as e:
            logger.error(f"Error in execute: {e}")
            return None
        
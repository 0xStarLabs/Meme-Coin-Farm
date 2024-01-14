import time
from loguru import logger
from config import CAPMONSTER_API_KEY
from utilities.constants import WEBSITE_URL, HCAPTCHA_KEY
from requests.exceptions import RequestException


class HCaptchaSolver:
    def __init__(self, wallet, client):
        self.wallet = wallet
        self.client = client

    def create_task(self) -> int:
        response: None = None

        while True:
            try:
                response = self.client.post(
                    url='https://api.capmonster.cloud/createTask',
                        json={
                            'clientKey': CAPMONSTER_API_KEY,
                            'task': {
                                'type': 'HCaptchaTaskProxyless',
                                'websiteURL': WEBSITE_URL,
                                'websiteKey': HCAPTCHA_KEY,
                                'fallbackToActualUA': True
                            }
                        })
                return response.json()['taskId']

            except Exception as error:
                if response:
                    logger.error(f'{self.wallet.address} | HCaptcha: {response.text()}')
                    time.sleep(5)
                else:
                    logger.error(f'{self.wallet.address} | HCaptcha: {error}')
                    time.sleep(5)


    def get_task_result(self, task_id: int | str) -> tuple[str, str] | None:
        while True:
            try:
                response = self.client.post(
                    url='https://api.capmonster.cloud/getTaskResult',
                    json={
                        'clientKey': CAPMONSTER_API_KEY,
                        'taskId': task_id
                    }
                )
                time.sleep(30)
                try:
                    response_data = response.json()
                except ValueError:
                    logger.error(f'{self.wallet.address} | Invalid JSON response: {response.text}')
                    time.sleep(5)
                    continue

                error_id = response_data.get('errorId')
                if error_id and error_id != 0:
                    logger.error(f'{self.wallet.address} | Error in response: {response.text}')
                    return

                solution = response_data.get('solution')
                if solution:
                    gRecaptchaResponse = solution.get('gRecaptchaResponse')
                    userAgent = solution.get('userAgent')
                    return gRecaptchaResponse, userAgent

            except RequestException as error:
                logger.error(f'{self.wallet.address} | Network error during HCaptcha verification: {error}')
                time.sleep(5)


    def hcaptcha_solver(self) -> tuple[str, str]:
        logger.info(f"{self.wallet.address} Started solving hcaptcha")
        while True:
            task_id: int = self.create_task()
            captcha_result: tuple[str, str] | None = self.get_task_result(task_id=task_id)
            if captcha_result:
                return captcha_result
            
import time
from loguru import logger
from config import CAPMONSTER_API_KEY
from utilities.constants import WEBSITE_URL, RECAPTCHA_KEY
from requests.exceptions import RequestException


class ReCaptchaSolver:
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
                                'type': 'RecaptchaV2Task',
                                'websiteURL': WEBSITE_URL,
                                'websiteKey': RECAPTCHA_KEY
                            }
                        })
                return response.json()['taskId']

            except Exception as error:
                if response:
                    logger.error(f'{self.wallet.address} | reCaptcha: {response.text()}')
                    time.sleep(5)
                else:
                    logger.error(f'{self.wallet.address} | reCaptcha: {error}')
                    time.sleep(5)


    def get_task_result(self, task_id: int | str) -> str | None:
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

                if response_data.get('errorId') != 0:
                    logger.error(f'{self.wallet.address} | Error response: {response.text}')
                    return

                solution = response_data.get('solution')
                if solution:
                    return solution.get('gRecaptchaResponse')

            except RequestException as error:

                logger.error(f'{self.wallet.address} | Network error during reCaptcha verification: {error}')
                time.sleep(5)


    def recaptcha_solver(self) -> str:
        logger.info(f"{self.wallet.address} Started solving recaptcha")
        while True:
            task_id: int =  self.create_task()
            captcha_result: str | None =  self.get_task_result(task_id=task_id)
            if captcha_result:
                return captcha_result
            
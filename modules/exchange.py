import ccxt
import random
import time
from loguru import logger

from config import API_KEY, SECRET_KEY, AMOUNT, MAX_FEE
from utilities.constants import ERC_20_ABI, MEME_ADDRESS


class Exchange():
    def __init__(self, address, w3) -> None:
        self.address = address
        self.w3 = w3
        self.exchange = ccxt.bingx({
            "apiKey": API_KEY,
            "secret": SECRET_KEY,
        })

    def withdraw(self):
        while True:
            try:
                fee = self.exchange.fetch_deposit_withdraw_fees(["MEME"])
                withdraw_min = float(fee['MEME']['info']['networkList'][0]['withdrawMin'])
                withdraw_fee = float(fee['MEME']['withdraw']['fee'])
                withdraw_enable = bool(fee['MEME']['info']['networkList'][0]['withdrawEnable'])

                if withdraw_fee < MAX_FEE and withdraw_min < MAX_FEE + AMOUNT[1] and withdraw_enable:
                    try:
                        contract = self.w3.eth.contract(address=self.w3.to_checksum_address(MEME_ADDRESS), abi=ERC_20_ABI)
                        initial_balance = contract.functions.balanceOf(self.address).call()

                        amount = withdraw_min + random.uniform(1, 10)
                        net_amount = amount - withdraw_fee
                        if net_amount < AMOUNT[0]:
                            to_add = random.uniform(AMOUNT[0] - net_amount, AMOUNT[1] - net_amount)
                            amount += to_add
                        logger.info(f"Sending {amount} MEME withdrawal request")
                        self.exchange.withdraw(
                            "MEME",
                            round(amount, 8),
                            self.address,
                            None,
                            {
                                'network': "ERC20",
                                'fee': withdraw_fee,
                                "pwd": '-'
                            })

                        while True:
                            time.sleep(60)
                            new_balance = contract.functions.balanceOf(self.address).call()

                            if new_balance > initial_balance:
                                logger.success(f"{amount} MEME Withdrawal arrived")
                                break
                            else:
                                print(f"Current balance: {new_balance} Waiting for withdrawal to arrive...")

                        break  # Break out of the outer loop if withdrawal is successful

                    except Exception as e:
                        logger.error(f"Error during withdrawal: {e}")
                        

                time.sleep(60)  # Wait before retrying to fetch fees

            except Exception as e:
                logger.error(f"Error fetching withdrawal fees: {e}")
                time.sleep(60)  # Wait before retrying to fetch fees

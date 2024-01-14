import sys
import urllib3
import time
import random
from eth_account import Account

from loguru import logger
from web3 import Web3

from concurrent.futures import ThreadPoolExecutor
from modules.exchange import Exchange
from modules.checker import Checker, save_private_keys_and_proxies as save_checker
from modules.register import Register, save_private_keys_and_proxies as save_registration
from utilities.common import read_files
from utilities.constants import MEME_ADDRESS, ERC_20_ABI 
from config import PAUSE, RPC, PRIVATE_KEYS_RANDOM_MOD


def execute_withdraw_and_register(exchange, register):
    try:
        # Perform withdraw and wait for its completion
        exchange.withdraw()
    except Exception as e:
        print(f"Error during withdraw: {e}")
    else:
        # Only if withdraw succeeds, submit register.execute
        register.execute()


def shuffle_together(arr1, arr2):
    combined = list(zip(arr1, arr2))
    random.shuffle(combined)
    return zip(*combined)


def configuration():
    urllib3.disable_warnings()
    logger.remove()
    logger.add(sys.stdout, colorize=True,
               format="<light-cyan>{time:HH:mm:ss}</light-cyan> | <level> {level: <8}</level> | - <white>{"
                      "message}</white>")


def main():
    configuration()
    private_keys, proxies = read_files()

    if PRIVATE_KEYS_RANDOM_MOD == "shuffle":
        private_keys, proxies = shuffle_together(private_keys, proxies)
    
    print("Choose an option:")
    print("1. Run checker")
    print("2. Run withdraw")
    print("3. Run register")
    print("4. Run withdraw and register")
    choice = int(input("Enter your choice: "))

    w3 = Web3(Web3.HTTPProvider(RPC))
    contract = w3.eth.contract(address=w3.to_checksum_address(MEME_ADDRESS), abi=ERC_20_ABI)
    
    num_threads = int(input("Enter the number of threads: "))

    if choice == 1:
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            for private_key, proxy in zip(private_keys, proxies):
                checker = Checker(private_key, proxy)
                executor.submit(checker.check)
                time.sleep(random.randint(PAUSE[0], PAUSE[1]))
        save_checker()

    elif choice == 2:
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            for private_key in private_keys:
                wallet = Account.from_key(private_key)
                exchange = Exchange(wallet.address, w3)
                executor.submit(exchange.withdraw)
                time.sleep(random.randint(PAUSE[0], PAUSE[1]))

    elif choice == 3:
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            for private_key, proxy in zip(private_keys, proxies):
                wallet = Account.from_key(private_key)
                balance = w3.from_wei(contract.functions.balanceOf(wallet.address).call(), "ether")
                if balance > 69:
                    register = Register(private_key, proxy)
                    executor.submit(register.execute)
                    time.sleep(random.randint(PAUSE[0], PAUSE[1]))
                else:
                    logger.error(f"{wallet.address} not enough balance: {balance}")
        save_registration()

    elif choice == 4:
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            for private_key, proxy in zip(private_keys, proxies):
                wallet = Account.from_key(private_key)
                balance = w3.from_wei(contract.functions.balanceOf(wallet.address).call(), "ether")
                register = Register(private_key, proxy)

                if balance < 69:
                    exchange = Exchange(wallet.address, w3)
                    # Submit a combined task of withdraw and register
                    executor.submit(execute_withdraw_and_register, exchange, register)
                else:
                    # Directly submit register.execute if balance is 69 or more
                    executor.submit(register.execute)

                time.sleep(random.randint(PAUSE[0], PAUSE[1]))
        save_registration()

    else:
        print("Not correct choice")

if __name__ == "__main__":
    main()

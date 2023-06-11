import json
import random
import requests
from tqdm import tqdm
from web3 import Web3
from info import *
import time
from loguru import logger
from eth_account.messages import encode_defunct
from fake_useragent import UserAgent
import pandas as pd
from config import *
class Help:
    def check_status_tx(self, tx_hash):
        logger.info(f'{self.address} - жду подтверждения транзакции...')

        while True:
            try:
                status = self.w3.eth.get_transaction_receipt(tx_hash)['status']
                if status in [0, 1]:
                    return status
                time.sleep(1)
            except Exception as error:
                time.sleep(1)

    def sleep_indicator(self, sec):
        for i in tqdm(range(sec), desc='жду', bar_format="{desc}: {n_fmt}c / {total_fmt}c {bar}", colour='green'):
            time.sleep(1)

class ZkMessage(Help):
    def __init__(self,privatekey,chain,to,delay,proxy=None):
        self.privatekey = privatekey
        self.chain = chain
        self.to = to
        self.w3 = Web3(Web3.HTTPProvider(rpcs[self.chain]))
        self.scan = scans[self.chain]
        self.account = self.w3.eth.account.from_key(self.privatekey)
        self.address = self.account.address
        self.delay = delay
        self.proxy = proxy

    def auth(self):
        ua = UserAgent()
        ua = ua.random
        headers = {
            'authority': 'api.zkbridge.com',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'content-type': 'application/json',
            'origin': 'https://zkbridge.com',
            'referer': 'https://zkbridge.com/',
            'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': ua,
        }

        json_data = {
            'publicKey': self.address.lower(),
        }

        while True:
            try:
                if self.proxy:
                    proxies = {'http': self.proxy, 'https': self.proxy}
                    response = requests.post(
                        'https://api.zkbridge.com/api/signin/validation_message',
                        json=json_data,     headers=headers,proxies=proxies
                    )
                else:
                    response = requests.post(
                        'https://api.zkbridge.com/api/signin/validation_message',
                        json=json_data,    headers=headers,

                    )

                if response.status_code == 200:
                    msg = json.loads(response.text)

                    msg = msg['message']
                    msg = encode_defunct(text=msg)
                    sign = self.w3.eth.account.sign_message(msg, private_key=self.privatekey)
                    signature = self.w3.to_hex(sign.signature)
                    json_data = {
                        'publicKey': self.address,
                        'signedMessage': signature,
                    }
                    return signature, ua
            except Exception as e:
                logger.error(f'{self.address}:{self.chain} - {e}')
                time.sleep(5)

    def sign(self):

        # sign msg
        signature, ua = self.auth()
        headers = {
            'authority': 'api.zkbridge.com',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'content-type': 'application/json',
            'origin': 'https://zkbridge.com',
            'referer': 'https://zkbridge.com/',
            'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': ua,
        }

        json_data = {
            'publicKey': self.address.lower(),
            'signedMessage': signature,
        }
        while True:
            try:

                if self.proxy:
                    proxies = {'http': self.proxy, 'https': self.proxy}

                    response = requests.post('https://api.zkbridge.com/api/signin', headers=headers, json=json_data, proxies=proxies)
                else:
                    response = requests.post('https://api.zkbridge.com/api/signin',  headers=headers, json=json_data)
                if response.status_code == 200:
                    token = json.loads(response.text)['token']
                    headers['authorization'] = f'Bearer {token}'
                    session = requests.session()
                    session.headers.update(headers)
                    return session

            except Exception as e:
                logger.error(F'{self.address}:{self.chain} - {e}')
                time.sleep(5)

    def profile(self):
        session = self.sign()
        params = ''
        try:
            if self.proxy:
                proxies = {'http': self.proxy, 'https': self.proxy}
                response = session.get('https://api.zkbridge.com/api/user/profile', params=params,proxies=proxies)
            else:
                response = session.get('https://api.zkbridge.com/api/user/profile', params=params)
            if response.status_code == 200:
                logger.success(f'{self.address}:{self.chain} - успешно авторизовался...')
                return session
        except Exception as e:
            logger.error(f'{self.address}:{self.chain} - {e}')
            return False

    def msg(self, session, contract_msg, msg, from_chain, to_chain,tx_hash):

        timestamp = time.time()

        json_data = {
            'message': msg,
            'mailSenderAddress': contract_msg,
            'receiverAddress': self.address,
            'receiverChainId': to_chain,
            'sendTimestamp': timestamp,
            'senderAddress': self.address,
            'senderChainId': from_chain,
            'senderTxHash': tx_hash,
            'sequence': random.randint(4500,5000),
            'receiverDomainName': '',
        }

        try:
            if self.proxy:
                proxies = {'http': self.proxy, 'https': self.proxy}
                response = session.get('https://api.zkbridge.com/api/user/profile', json=json_data,proxies=proxies)
            else:
                response = session.get('https://api.zkbridge.com/api/user/profile', json=json_data)
            if response.status_code == 200:
                logger.success(f'{self.address}:{self.chain} - cообщение подтвержденно...')
                return True


        except Exception as e:
            logger.error(f'{self.address}:{self.chain} - {e}')
            return False
    def create_msg(self):
        n = random.randint(1, 10)
        string = []
        word_site = "https://www.mit.edu/~ecprice/wordlist.10000"
        response = requests.get(word_site)
        for i in range(n):
            WORDS = [g for g in response.text.split()]
            string.append(random.choice(WORDS))

        msg = ' '.join(string)
        return msg

    def send_msg(self):
        data = self.profile()
        if data:
            session = data
        else:
            return False
        contract_msg = Web3.to_checksum_address(sender_msgs[self.chain])
        lz_id = stargate_ids[self.to]
        to_chain_id = chain_ids[self.to]
        from_chain_id = chain_ids[self.chain]
        message = self.create_msg()
        dst_address = Web3.to_checksum_address(dst_addresses[self.to])
        lzdst_address = Web3.to_checksum_address(lzdst_addresses[self.to])

        mailer = self.w3.eth.contract(address=contract_msg,abi=abi)
        while True:
            try:
                tx = mailer.functions.sendMessage(to_chain_id,dst_address,lz_id,lzdst_address,0,self.address,message).build_transaction({
                    'from': self.address,
                    'value':fee[self.chain],
                    'gas':mailer.functions.sendMessage(to_chain_id,dst_address,lz_id,lzdst_address,0,self.address,message).estimate_gas({'from': self.address, 'nonce': self.w3.eth.get_transaction_count(self.address),'value':fee[self.chain]}),
                    'nonce': self.w3.eth.get_transaction_count(self.address),
                    'gasPrice': self.w3.eth.gas_price
                })

                if self.chain != 'bsc':
                    tx['gasPrice'] = self.w3.eth.gas_price
                else:
                    tx['gasPrice'] = int(1.5 * 10 ** 9)
                logger.info(f'{self.address}:{self.chain} - начинаю отправку сообщения в {self.to}...')
                sign = self.account.sign_transaction(tx)
                hash = self.w3.eth.send_raw_transaction(sign.rawTransaction)
                status = self.check_status_tx(hash)
                self.sleep_indicator(5)
                if status == 1:
                    logger.success(f'{self.address}:{self.chain} - успешно отправил сообщение {message} в {self.to} : {self.scan}{self.w3.to_hex(hash)}...')
                    time.sleep(5)
                    msg = self.msg(session,contract_msg,message,from_chain_id,to_chain_id,self.w3.to_hex(hash))
                    if msg:
                        logger.success(f'f{self.address} - success')
                        self.sleep_indicator(random.randint(self.delay[0],self.delay[1]))
                        return self.address, 'success'

            except Exception as e:
                error = str(e)
                if 'INTERNAL_ERROR: insufficient funds' in error or 'insufficient funds for gas * price + value' in error:
                    logger.error(f'{self.address}:{self.chain} - не хватает денег на газ, заканчиваю работу через 5 секунд...')
                    time.sleep(5)
                    return self.address, 'error'
                else:
                    logger.error(f'{self.address}:{self.chain} - {e}...')
                    time.sleep(2)
                    return self.address, 'error'
def main():
    print(f'\n{" "*32}автор - https://t.me/iliocka{" "*32}\n')
    wallets, results =[], []
    successes, errors = 0, 0
    for key in keys:
        if proxies:
            proxy = random.choice(proxies)
        else:
            proxy = None
        msg = ZkMessage(key, chain_from, chain_to, DELAY, proxy)
        res = msg.send_msg()
        wallets.append(res[0]), results.append(res[1])
        if res[1] == 'success':
            successes += 1
        else:
            errors += 1
    res = {'address': wallets, 'result': results}
    df = pd.DataFrame(res)
    df.to_csv('results.csv', index=False)
    print()
    logger.success(f'Отправка сообщений закончена...\nУспешно - {successes}:{len(keys)}\nНеуспешно - {errors}:{len(keys)}')


if __name__ == '__main__':
    main()
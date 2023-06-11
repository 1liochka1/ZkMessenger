'''


в proxyy.txt прокси с новой строки в формате - http://login:pass@ip:port

в keys приватники с новой строки

delay - от и до скольки секунд между кошельками

chain from - из какой сети сообщение - ТОЛЬКО ИЗ BSC И POLYGON !!!
сhain to - куда
'''
import random

with open("keys.txt", "r") as f:
    keys = [row.strip() for row in f]
    random.shuffle(keys)

with open("proxyy.txt", "r") as f:
    proxies = [row.strip() for row in f]

chain_from = ''  #bsc, polygon
chain_to = ''    #bsc, polygon, ftm
DELAY = (0, 100)

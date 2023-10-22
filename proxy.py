import requests
from termcolor import colored
from configparser import ConfigParser
from re import compile
from time import sleep
import os
import threading

PROXIES_TYPES = ('http', 'socks4', 'socks5')

REGEX = compile(r"(?:^|\D)?((" + r"(?:[1-9]|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"):" + (r"(?:\d|[1-9]\d{1,3}|[1-5]\d{4}|6[0-4]\d{3}"
                + r"|65[0-4]\d{2}|655[0-2]\d|6553[0-5])")
                + r")(?:\D|$)")

errors = open('errors.txt', 'a+')
http_proxies, socks4_proxies, socks5_proxies = [], [], []
proxy_error = 0

cfg = ConfigParser(interpolation=None)
cfg.read("config.ini", encoding="utf-8")

try:
    http, socks4, socks5 = cfg["HTTP"], cfg["SOCKS4"], cfg["SOCKS5"]
except KeyError:
    print(' [ OUTPUT ] Error | config.ini not found!')
    sleep(3)
    exit()

def scrap(sources, _proxy_type):
    global proxy_error
    for source in sources:
        if source:
            try:
                response = requests.get(source, timeout=15)
                if tuple(REGEX.finditer(response.text)):
                    for proxy in tuple(REGEX.finditer(response.text)):
                        if _proxy_type == 'http':
                            http_proxies.append(proxy.group(1))
                        elif _proxy_type == 'socks4':
                            socks4_proxies.append(proxy.group(1))
                        elif _proxy_type == 'socks5':
                            socks5_proxies.append(proxy.group(1))
            except Exception as e:
                errors.write(f'{e}\n')
                proxy_error += 1

def start_scrap():
    for i in (http_proxies, socks4_proxies, socks5_proxies):
        i.clear()
    for source_list, proxy_type in ((http.get("Sources").splitlines(), 'http'),
                                    (socks4.get("Sources").splitlines(), 'socks4'),
                                    (socks5.get("Sources").splitlines(), 'socks5')):
        scrap(source_list, proxy_type)

def check_proxy(proxy, live_proxies):
    url = "https://www.google.com"
    proxies = {
        "http": proxy,
        "https": proxy
    }

    try:
        response = requests.get(url, proxies=proxies, timeout=5)
        if response.status_code == 200:
            if proxy not in live_proxies:
                with open("live.txt", "a") as file:
                    file.write(proxy + "\n")
                live_proxies.add(proxy)
                print(colored(f"Proxy {proxy} bekerja dengan baik. Disimpan.", "green"))

                # Add threading for 100 additional requests here
                threads = []
                for _ in range(100):
                    thread = threading.Thread(target=make_additional_request, args=(proxy, proxies))
                    threads.append(thread)
                    thread.start()
                for thread in threads:
                    thread.join()

            else:
                print(colored(f"Proxy {proxy} sudah ada dalam daftar live proxies.", "yellow"))
        else:
            print(colored(f"Proxy {proxy} memberikan respons tidak valid.", "yellow"))
    except requests.RequestException:
        print(colored(f"Proxy {proxy} tidak berfungsi.", "red"))

def make_additional_request(proxy, proxies):
    try:
        response = requests.get("https://sxtcp.tg-index.workers.dev", proxies=proxies, timeout=5)
        # Handle the response as needed
    except requests.RequestException:
        pass

def main():
    proxy_list_file = "proxy.txt"
    live_proxies = set()

    if os.path.exists(proxy_list_file):
        os.remove(proxy_list_file)
        
    start_scrap()
    with open(proxy_list_file, "w") as file:
        for proxy in http_proxies + socks4_proxies + socks5_proxies:
            file.write(proxy + "\n")
    
    with open(proxy_list_file, "r") as file:
        proxies = file.readlines()

    for proxy in proxies:
        proxy = proxy.strip()
        check_proxy(proxy, live_proxies)

if __name__ == "__main__":
    main()

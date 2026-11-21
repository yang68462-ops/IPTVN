#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直播源健康报告（只报告，不删除）。

原因：海外 runner 无法判断国内源的真实存活状态——被地域屏蔽的源
会对海外 IP 返回 404，但在国内可以正常播放。自动删除会误杀大量
可用源，所以这个脚本只打印可疑链接，不修改任何文件。

用法: python3 scripts/check_streams.py IPTV.m3u IPV4.m3u Adult.m3u
"""
import re
import sys
import socket
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor

TIMEOUT = 10
WORKERS = 20


def check(url):
    """返回 True=存活, False=可疑, None=未测(IPv6)"""
    url = url.strip()
    if not url or url.startswith('#'):
        return True
    host = re.sub(r'^[a-zA-Z][a-zA-Z0-9+.\-]*://', '', url).split('/')[0].split('@')[-1]
    if host.startswith('['):  # IPv6 字面地址，runner 测不了
        return None
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}, method='GET')
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            if r.status in (404, 410):
                return False
            r.read(2048)
            return True
    except urllib.error.HTTPError as e:
        return False if e.code in (404, 410) else True
    except urllib.error.URLError as e:
        if isinstance(e.reason, socket.gaierror):
            return False
        return True
    except Exception:
        return True


def process(path):
    with open(path, encoding='utf-8', errors='ignore') as f:
        lines = f.read().splitlines()
    urls = [l for l in lines if l and not l.startswith('#')]
    seen, uniq = set(), []
    for u in urls:
        if u not in seen:
            seen.add(u)
            uniq.append(u)
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        results = list(ex.map(check, uniq))
    alive = sum(1 for ok in results if ok is True)
    dead = sum(1 for ok in results if ok is False)
    skipped = sum(1 for ok in results if ok is None)
    print(f'{path}: 存活 {alive}，可疑 {dead}（仅报告，未删除），未测(IPv6) {skipped}')
    for u, ok in zip(uniq, results):
        if ok is False:
            print(f'  可疑: {u[:100]}')


if __name__ == '__main__':
    for p in sys.argv[1:]:
        process(p)

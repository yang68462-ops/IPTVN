#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
点播站存活巡检：逐个请求 sites.json 里每个站的数据接口，只报告、不删除。
- type 0/1（采集 API）：GET api?ac=list，校验 JSON code==1 且 list 非空
- type 3（爬虫站）：校验 spider jar 能下载、ext 地址能访问（深层可用性需电视端实测）
用法：python3 scripts/check_vod_sites.py
"""
import json
import os
import sys
import urllib.request
import urllib.error

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TIMEOUT = 20
UA = {"User-Agent": "okhttp/3.12.0"}


def http_ok(url):
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.status, r.read(65536)
    except urllib.error.HTTPError as e:
        return e.code, b""
    except Exception as e:
        return 0, str(e).encode()


def check_cms(site):
    api = site["api"]
    sep = "&" if "?" in api else "?"
    url = api + sep + "ac=list"
    status, body = http_ok(url)
    if status != 200:
        return False, f"HTTP {status}"
    if "xml" in api.lower():
        # type 0 的 XML 采集接口：校验返回是 XML 且含数据节点
        head = body[:500].lower()
        if b"<?xml" in head or b"<rss" in head:
            return True, "XML 接口正常"
        return False, "返回不是 XML"
    try:
        d = json.loads(body)
    except Exception:
        return False, "返回不是 JSON"
    if not isinstance(d, dict) or d.get("code") != 1:
        return False, f"code={d.get('code') if isinstance(d, dict) else '?'}"
    lst = d.get("list") or []
    if not lst:
        return False, "list 为空"
    return True, f"total={d.get('total', '?')}"


def check_spider(site, spider_jar):
    problems = []
    jar_url = site.get("jar") or spider_jar
    if jar_url:
        jar_url = jar_url.split(";")[0]
        status, body = http_ok(jar_url)
        if status != 200 or not body.startswith(b"PK"):
            problems.append(f"jar 不可下载（HTTP {status}）")
    ext = site.get("ext")
    if isinstance(ext, str) and ext.startswith("http"):
        status, _ = http_ok(ext)
        if status != 200:
            problems.append(f"ext 不可访问（HTTP {status}）")
    if problems:
        return False, "；".join(problems)
    return True, "jar/ext 可访问（深层可用性需电视端实测）"


def main():
    with open(os.path.join(REPO, "sites.json"), encoding="utf-8") as f:
        cfg = json.load(f)
    sites = cfg["sites"]
    spider_jar = cfg.get("spider", "")

    alive, dead = [], []
    for s in sites:
        name = s.get("name", s.get("key", "?"))
        t = s.get("type")
        try:
            if t in (0, 1):
                ok, msg = check_cms(s)
            elif t == 3:
                ok, msg = check_spider(s, spider_jar)
            else:
                ok, msg = False, f"未知 type={t}"
        except Exception as e:
            ok, msg = False, f"异常：{e}"
        (alive if ok else dead).append((name, msg))
        print(f"[{'OK' if ok else 'FAIL'}] {name} —— {msg}", flush=True)

    print(f"\n共 {len(sites)} 个站：存活 {len(alive)}，疑似失效 {len(dead)}")
    if dead:
        print("失效列表：" + "、".join(n for n, _ in dead))
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
根据仓库里的 m3u 文件和 sites.json 自动生成 tvbox.json。
只有 NAME_MAP 里登记过的文件才会进入 lives，保证电视端看到的分组稳定；
新出现的 m3u 文件会打印提示，不会自动加进去。
"""
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GH_PROXY = 'https://gh-proxy.com/https://raw.githubusercontent.com/yang68462-ops/IPTVN/Files/'

# (文件名, 电视上显示的名字, 是否挂EPG)
NAME_MAP = [
    ('IPTV.m3u', '央视卫视', True),
    ('IPV4.m3u', '央视卫视-IPv4', False),
    ('CCTV.m3u', '央视', False),
    ('CNTV.m3u', '卫视', False),
    ('GAT.m3u', '港澳台', False),
    ('Adult.m3u', '成人', False),
]


def main():
    with open(os.path.join(REPO, 'sites.json'), encoding='utf-8') as f:
        sites_cfg = json.load(f)
    lives = []
    for fname, name, with_epg in NAME_MAP:
        if not os.path.exists(os.path.join(REPO, fname)):
            print(f'跳过缺失文件: {fname}')
            continue
        entry = {'name': name, 'url': GH_PROXY + fname}
        if with_epg and os.path.exists(os.path.join(REPO, 'EPG.xml')):
            entry['epg'] = GH_PROXY + 'EPG.xml'
        lives.append(entry)
    known = {f for f, _, _ in NAME_MAP}
    for f in sorted(os.listdir(REPO)):
        if f.endswith('.m3u') and f not in known:
            print(f'发现未登记的 {f}，未加入 tvbox.json（如需加入请告诉助手）')
    config = {
        'spider': sites_cfg['spider'],
        'sites': sites_cfg['sites'],
        'lives': lives,
    }
    with open(os.path.join(REPO, 'tvbox.json'), 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    print(f'tvbox.json 已生成：{len(lives)} 组直播，{len(config["sites"])} 个点播站')


if __name__ == '__main__':
    main()

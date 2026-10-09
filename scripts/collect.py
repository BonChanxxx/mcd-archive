#!/usr/bin/env python3
"""采集麦当劳账号数据 → 本地 JSON 目录（含个人数据，切勿公开）

用法:
    python3 collect.py [输出目录]     # 默认 ../private/data/raw
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcd_client import McdMcpClient

CALLS = [
    ('now-time-info', {}, 'time.json'),
    ('query-my-account', {}, 'account.json'),
    ('query-my-coupons', {}, 'my-coupons.json'),
    ('available-coupons', {}, 'available-coupons.json'),
    ('query-lottery-info', {}, 'lottery.json'),
    ('query-my-prizes', {'pageNum': '1', 'pageSize': '50'}, 'my-prizes.json'),
    ('order-list', {}, 'orders.json'),
    ('campaign-calendar', {}, 'campaigns.json'),
    ('mall-points-products', {}, 'mall.json'),
    ('list-nutrition-foods', {}, 'nutrition.json'),
]


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'raw')
    out = os.path.abspath(out)
    os.makedirs(out, exist_ok=True)

    client = McdMcpClient()
    ok, fail = 0, 0
    for tool, args, fn in CALLS:
        try:
            data = client.call_data(tool, args)
            with open(os.path.join(out, fn), 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=1)
            print(f'OK   {tool:22s} -> {fn}')
            ok += 1
        except Exception as e:
            print(f'FAIL {tool:22s} : {e}')
            fail += 1
        time.sleep(0.25)
    print(f'\n完成：{ok} 成功 / {fail} 失败 → {out}')


if __name__ == '__main__':
    main()

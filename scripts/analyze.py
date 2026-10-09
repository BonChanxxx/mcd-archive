#!/usr/bin/env python3
"""分析引擎：把采集的原始数据计算为「麦麦档案」派生指标 → profile.json

用法:
    python3 analyze.py [数据目录] [输出文件]
    默认: ../private/data/raw  →  ../private/data/profile.json
"""
import json
import os
import sys
from collections import Counter
from datetime import datetime


def load(raw_dir, fn):
    p = os.path.join(raw_dir, fn + '.json')
    if not os.path.exists(p):
        return None
    with open(p, encoding='utf-8') as f:
        return json.load(f)


def parse_orders(d):
    """订单 → 结构化列表"""
    if not d:
        return []
    lst = (d.get('data') or {}).get('list') or []
    out = []
    for o in lst:
        items = []
        for p in o.get('orderProductList') or []:
            combo = '＋'.join([c.get('name', '') for c in (p.get('comboItemList') or [])])
            items.append({'name': p.get('productName', ''), 'qty': p.get('quantity', 1), 'combo': combo})
        amt = o.get('realTotalAmount')
        try:
            amount = round(float(amt), 2) if amt not in (None, '') else 0.0
        except (TypeError, ValueError):
            amount = 0.0
        ct = o.get('createTime') or ''
        hour = None
        if len(ct) >= 13 and ct[11:13].isdigit():
            hour = int(ct[11:13])
        out.append({
            'time': ct,
            'date': ct[:10],
            'hour': hour,
            'store': o.get('storeName', ''),
            'items': items,
            'amount': amount,
        })
    out.sort(key=lambda x: x['time'], reverse=True)
    return out


def parse_account(d):
    if not d:
        return {}
    a = d.get('data') or {}
    def num(x):
        try:
            return float(x)
        except (TypeError, ValueError):
            return 0.0
    return {
        'available': num(a.get('availablePoint')),
        'accumulated': num(a.get('accumulativePoint')),
        'used': num(a.get('usedPoint')),
        'expiring': num(a.get('currentMouthExpirePoint')),
    }


def parse_coupons(d):
    if not d:
        return []
    cs = (d.get('data') or {}).get('coupons') or []
    out = []
    for c in cs:
        out.append({
            'title': c.get('title') or c.get('couponName') or '',
            'valid': c.get('validTime') or c.get('validDate') or c.get('useTime') or '',
        })
    return out


def parse_prizes(d):
    if not d:
        return []
    prz = (d.get('data') or {}).get('prizes') or []
    return [{'name': p.get('name', ''), 'time': (p.get('recordTime') or '')[:10],
             'type': p.get('prizeTypeText', '')} for p in prz]


def parse_lottery(d):
    if not d:
        return {}
    a = d.get('data') or {}
    def num(x):
        try:
            return float(x)
        except (TypeError, ValueError):
            return 0.0
    return {
        'name': a.get('activityName', ''),
        'status': a.get('activityStatusText', ''),
        'cost_per_draw': num(a.get('drawPoint')),
        'prizes_count': len(a.get('prizes') or []),
    }


def parse_mall(d):
    if not d:
        return []
    items = d.get('data') or []
    out = []
    for i in items:
        try:
            pt = float(i.get('point') or 0)
        except (TypeError, ValueError):
            pt = 0
        if pt > 0:
            out.append({'name': i.get('spuName', ''), 'points': pt})
    return out


def compute(orders, account, coupons, prizes, lottery, mall):
    # ---- 总览 ----
    total_spent = round(sum(o['amount'] for o in orders), 2)
    zero_orders = [o for o in orders if o['amount'] == 0]
    stores = Counter(o['store'] for o in orders if o['store'])
    dates = sorted([o['date'] for o in orders if o['date']])

    # ---- 习惯 ----
    hours = [o['hour'] for o in orders if o['hour'] is not None]
    morning = [h for h in hours if h < 10]
    noon = [h for h in hours if 10 <= h < 14]
    evening = [h for h in hours if h >= 17]
    combo_orders = [o for o in orders if any('随心配' in i['name'] or '1+1' in i['name'] for i in o['items'])]
    all_product_names = []
    for o in orders:
        for i in o['items']:
            all_product_names.append(i['name'])
    max_order = max(orders, key=lambda x: x['amount']) if orders else None
    merch_orders = [o for o in orders if any(('包' in i['name'] or '周边' in i['name']) and '套餐' not in i['name'] for i in o['items'])]

    # ---- 收藏（门票）----
    tickets = [p for p in prizes if '门票' in (p.get('type') or '')]
    ticket_span = ''
    if tickets:
        ts = sorted([p['time'] for p in tickets if p['time']])
        if ts:
            ticket_span = f"{ts[0]} ~ {ts[-1]}"

    # ---- 成就判定（规则库：17 条，便于扩展；输出已解锁 + 待解锁）----
    distinct_products = len(set(all_product_names))
    top_store_cnt = stores.most_common(1)[0][1] if stores else 0
    max_amount = max((o['amount'] for o in orders), default=0)
    acc = (account or {}).get('accumulated', 0)
    cost = (lottery or {}).get('cost_per_draw') or 0
    draws = int((account or {}).get('available', 0) // cost) if cost else 0
    order_days = 0
    if orders:
        ds = sorted([o['date'] for o in orders if o['date']])
        try:
            order_days = (datetime.strptime(ds[-1], '%Y-%m-%d') - datetime.strptime(ds[0], '%Y-%m-%d')).days
        except Exception:
            order_days = 0
    ticket_months = 0
    if tickets:
        ts = sorted([p['time'] for p in tickets if p['time']])
        if ts:
            try:
                ticket_months = max(0, int((datetime.strptime(ts[-1], '%Y-%m-%d') - datetime.strptime(ts[0], '%Y-%m-%d')).days / 30.44))
            except Exception:
                ticket_months = 0

    rules = [
        ('first', '初遇时刻', 'bronze', len(orders) >= 1, '档案从第 1 笔订单开始'),
        ('solar', '节气收藏家', 'gold', len(tickets) >= 8, f'收集 {len(tickets)} 张活动门票，一期不落'),
        ('zero', '免单猎人', 'gold', len(zero_orders) >= 1, f'{len(zero_orders)} 笔订单实付 ¥0，券用出了艺术'),
        ('earlybird', '早餐征服者', 'silver', len(morning) >= 3, f'{len(morning)} 顿在上午 10 点前解决'),
        ('nooner', '午间玩家', 'silver', len(noon) >= 3, f'{len(noon)} 顿踩准午餐时段'),
        ('night', '夜宵搭子', 'bronze', len(evening) >= 1, '深夜的麦当劳也有你的身影'),
        ('combo', '随心配大师', 'gold', len(combo_orders) >= 3, f'{len(combo_orders)} 单锁定 1+1/随心配组合'),
        ('cross', '跨界打卡', 'silver', len(stores) >= 2, f'在 {len(stores)} 家麦当劳留下足迹'),
        ('loyal', '专一食客', 'silver', top_store_cnt >= 10, f'同一家店吃了 {top_store_cnt} 顿'),
        ('merch', '周边猎人', 'bronze', len(merch_orders) >= 1, '下单带走联名周边'),
        ('big', '一掷千金', 'bronze', max_amount >= 50, f'单笔最高 ¥{max_amount:.1f}'),
        ('coupon', '券包富人', 'silver', len(coupons) >= 10, f'手握 {len(coupons)} 张待用券'),
        ('variety', '菜单探索家', 'bronze', distinct_products >= 15, f'尝过 {distinct_products} 种单品'),
        ('span', '长情陪伴', 'silver', order_days >= 30, f'有记录的日子横跨 {order_days} 天'),
        ('points', '积分大亨', 'gold', acc >= 10000, f'累计获得 {acc:.0f} 积分'),
        ('lottery', '抽奖大户', 'silver', draws >= 50, f'积分够抽 {draws} 次奖'),
        ('veteran', '麦麦老友', 'gold', ticket_months >= 6, f'门票收藏线横跨 {ticket_months} 个月'),
    ]
    lv_order = {'gold': 0, 'silver': 1, 'bronze': 2}
    achievements = [{'id': i, 'name': n, 'level': lv, 'desc': d} for i, n, lv, ok, d in rules if ok]
    achievements.sort(key=lambda a: lv_order.get(a['level'], 3))
    locked = [{'id': i, 'name': n, 'level': lv} for i, n, lv, ok, d in rules if not ok]

    # ---- 人设 ----
    tags = []
    if len(morning) >= 3:
        tags.append('晨间型选手')
    if len(combo_orders) >= 3:
        tags.append('组合优化家')
    if tickets and len(tickets) >= 4:
        tags.append('收藏控')
    if zero_orders:
        tags.append('羊毛大师')
    fav_store = stores.most_common(1)[0] if stores else ('', 0)

    # ---- 资产 ----
    assets = {}
    if account:
        cost = lottery.get('cost_per_draw') or 0
        assets = {
            'points': account,
            'affordable_draws': int(account['available'] // cost) if cost else 0,
            'coupons_count': len(coupons),
            'lottery': lottery,
        }
        # 商城里程碑：找可兑换与下一个里程碑
        redeemable = [m for m in mall if m['points'] <= account['available']]
        next_up = [m for m in mall if m['points'] > account['available']]
        next_up.sort(key=lambda m: m['points'])
        assets['redeemable_now'] = sorted(redeemable, key=lambda m: -m['points'])[:3]
        assets['next_milestone'] = next_up[0] if next_up else None
        assets['milestone_gap'] = round(next_up[0]['points'] - account['available'], 1) if next_up else None

    return {
        'meta': {
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'orders_count': len(orders),
            'date_range': f"{dates[0]} ~ {dates[-1]}" if dates else '',
        },
        'overview': {
            'orders_count': len(orders),
            'total_spent': total_spent,
            'stores_count': len(stores),
            'zero_orders': len(zero_orders),
            'tickets_count': len(tickets),
            'avg_amount': round(total_spent / len(orders), 2) if orders else 0,
        },
        'habits': {
            'morning': len(morning), 'noon': len(noon), 'evening': len(evening),
            'fav_store': fav_store[0], 'fav_store_count': fav_store[1],
            'combo_orders': len(combo_orders),
            'max_order': ({'amount': max_order['amount'], 'date': max_order['date'],
                           'items': [i['name'] for i in max_order['items']]} if max_order else None),
        },
        'collection': {'tickets_count': len(tickets), 'span': ticket_span,
                       'tickets': sorted(tickets, key=lambda p: p['time'])},
        'achievements': achievements,
        'locked_achievements': locked,
        'persona': {'tags': tags},
        'assets': assets,
    }


def main():
    base = os.path.dirname(os.path.abspath(__file__))
    raw = sys.argv[1] if len(sys.argv) > 1 else os.path.join(base, '..', 'data', 'raw')
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(base, '..', 'data', 'profile.json')
    raw, out = os.path.abspath(raw), os.path.abspath(out)

    orders = parse_orders(load(raw, 'orders'))
    account = parse_account(load(raw, 'account'))
    coupons = parse_coupons(load(raw, 'my-coupons'))
    prizes = parse_prizes(load(raw, 'my-prizes'))
    lottery = parse_lottery(load(raw, 'lottery'))
    mall = parse_mall(load(raw, 'mall'))

    profile = compute(orders, account, coupons, prizes, lottery, mall)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)
    print(json.dumps(profile, ensure_ascii=False, indent=1))
    print(f'\n→ saved: {out}')


if __name__ == '__main__':
    main()

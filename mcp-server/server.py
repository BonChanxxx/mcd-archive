#!/usr/bin/env python3
"""mcd-profile · 麦当劳档案 MCP Server

「麦麦档案」（mcd-archive）的 MCP Server 形态：基于麦当劳官方 MCP
（https://mcp.mcd.cn）的轻量档案查询服务，把账号数据（订单/门票/积分/
券/奖品/成就）以标准 MCP 工具暴露给任何 MCP 客户端。

四个工具：
  get_profile_summary   档案摘要（订单/门店/积分/门票/券/奖品总览）
  get_tickets           节气门票收藏线
  get_achievements      成就徽章（17 条规则，已解锁 + 待解锁）
  get_points_status     积分资产体检（可用/累计/抽奖/奖品）

用法：
  pip install -r requirements.txt
  MCD_TOKEN=<你的麦当劳 MCP Token> python3 server.py   # stdio 模式

数据安全：全部走麦当劳官方 MCP 只读接口；Token 仅从环境变量读取；
本服务不在任何位置存储或上传你的数据。
"""
import os
import sys
import time
from collections import Counter
from datetime import datetime

# 复用仓库内的零依赖 MCP 客户端（scripts/mcd_client.py）
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts'))
from mcd_client import McdMcpClient

from mcp.server.fastmcp import FastMCP

mcp = FastMCP('mcd-profile')

# ---------------------------------------------------------------------------
# 解析层：与 scripts/analyze.py 保持一致的归一化逻辑
# ---------------------------------------------------------------------------

def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def parse_orders(d):
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
            'time': ct, 'date': ct[:10], 'hour': hour,
            'store': o.get('storeName', ''), 'items': items, 'amount': amount,
        })
    out.sort(key=lambda x: x['time'], reverse=True)
    return out


def parse_account(d):
    if not d:
        return {}
    a = d.get('data') or {}
    return {
        'available': _num(a.get('availablePoint')),
        'accumulated': _num(a.get('accumulativePoint')),
        'used': _num(a.get('usedPoint')),
        'expiring': _num(a.get('currentMouthExpirePoint')),
    }


def parse_coupons(d):
    if not d:
        return []
    cs = (d.get('data') or {}).get('coupons') or []
    return [{'title': c.get('title') or c.get('couponName') or ''} for c in cs]


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
    return {
        'name': a.get('activityName', ''),
        'status': a.get('activityStatusText', ''),
        'cost_per_draw': _num(a.get('drawPoint')),
    }


# ---------------------------------------------------------------------------
# 数据访问层（容错：单个接口失败不影响其他工具）
# ---------------------------------------------------------------------------

_client = None


def client():
    global _client
    if _client is None:
        _client = McdMcpClient()
    return _client


def _fetch(tool, args=None):
    try:
        return client().call_data(tool, args or {})
    except Exception:
        return None


_cache = {'data': None, 'ts': 0.0}
_CACHE_TTL = 60.0


def _load_all():
    """一次性拉取档案所需的全部原始数据（归一化后返回）。

    带 60s 会话内缓存：多个工具连续调用时复用同一批数据，
    避免对官方 MCP 的重复请求（4 个工具全问 = 5~6 次 RPC，而非 20+ 次）。
    """
    now = time.time()
    if _cache['data'] is not None and now - _cache['ts'] < _CACHE_TTL:
        return _cache['data']
    data = {
        'orders': parse_orders(_fetch('order-list') or {}),
        'account': parse_account(_fetch('query-my-account') or {}),
        'coupons': parse_coupons(_fetch('query-my-coupons') or {}),
        'prizes': parse_prizes(_fetch('query-my-prizes', {'pageNum': '1', 'pageSize': '50'}) or {}),
        'lottery': parse_lottery(_fetch('query-lottery-info') or {}),
    }
    _cache['data'] = data
    _cache['ts'] = now
    return data


def _tickets_of(prizes):
    return [p for p in prizes if '门票' in (p.get('type') or '')]


def _ticket_months(tickets):
    ts = sorted([p['time'] for p in tickets if p['time']])
    if len(ts) < 2:
        return 0
    try:
        return max(0, int((datetime.strptime(ts[-1], '%Y-%m-%d')
                           - datetime.strptime(ts[0], '%Y-%m-%d')).days / 30.44))
    except ValueError:
        return 0


# ---------------------------------------------------------------------------
# 成就规则（与 scripts/analyze.py 的 17 条一致，便于扩展）
# ---------------------------------------------------------------------------

def evaluate_achievements(orders, coupons, tickets, account, lottery):
    hours = [o['hour'] for o in orders if o['hour'] is not None]
    morning = [h for h in hours if h < 10]
    noon = [h for h in hours if 10 <= h < 14]
    evening = [h for h in hours if h >= 17]
    combo_orders = [o for o in orders
                    if any('随心配' in i['name'] or '1+1' in i['name'] for i in o['items'])]
    all_product_names = [i['name'] for o in orders for i in o['items']]
    stores = Counter(o['store'] for o in orders if o['store'])
    zero_orders = [o for o in orders if o['amount'] == 0]
    merch_orders = [o for o in orders
                    if any(('包' in i['name'] or '周边' in i['name']) and '套餐' not in i['name']
                           for i in o['items'])]
    top_store_cnt = stores.most_common(1)[0][1] if stores else 0
    max_amount = max((o['amount'] for o in orders), default=0)
    # 与 analyze.py 一致：span 用首末订单的日期跨度，而非去重天数
    _dates = sorted([o['date'] for o in orders if o['date']])
    try:
        order_days = (datetime.strptime(_dates[-1], '%Y-%m-%d')
                      - datetime.strptime(_dates[0], '%Y-%m-%d')).days if len(_dates) >= 2 else 0
    except ValueError:
        order_days = 0
    draws = int(account.get('available', 0) / lottery['cost_per_draw']) \
        if lottery.get('cost_per_draw') else 0
    ticket_months = _ticket_months(tickets)

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
        ('variety', '菜单探索家', 'bronze', len(set(all_product_names)) >= 15,
         f'尝过 {len(set(all_product_names))} 种单品'),
        ('span', '长情陪伴', 'silver', order_days >= 30, f'有记录的日子横跨 {order_days} 天'),
        ('points', '积分大亨', 'gold', account.get('accumulated', 0) >= 10000,
         f'累计获得 {account.get("accumulated", 0):.0f} 积分'),
        ('lottery', '抽奖大户', 'silver', draws >= 50, f'积分够抽 {draws} 次奖'),
        ('veteran', '麦麦老友', 'gold', ticket_months >= 6, f'门票收藏线横跨 {ticket_months} 个月'),
    ]
    lv_order = {'gold': 0, 'silver': 1, 'bronze': 2}
    unlocked = [{'id': i, 'name': n, 'level': lv, 'desc': d}
                for i, n, lv, ok, d in rules if ok]
    unlocked.sort(key=lambda a: lv_order.get(a['level'], 3))
    locked = [{'id': i, 'name': n, 'level': lv} for i, n, lv, ok, d in rules if not ok]
    return unlocked, locked


# ---------------------------------------------------------------------------
# MCP 工具定义
# ---------------------------------------------------------------------------

@mcp.tool()
def get_profile_summary() -> dict:
    """获取麦当劳档案摘要：订单数/门店数/总消费/积分/门票/优惠券/奖品总览"""
    d = _load_all()
    orders, prizes = d['orders'], d['prizes']
    tickets = _tickets_of(prizes)
    dates = sorted([o['date'] for o in orders if o['date']])
    stores = {o['store'] for o in orders if o['store']}
    return {
        'orders': {
            'count': len(orders),
            'total_amount': round(sum(o['amount'] for o in orders), 2),
            'stores': len(stores),
            'first_order': dates[0] if dates else None,
            'last_order': dates[-1] if dates else None,
        },
        'points': {
            'available': d['account'].get('available', 0),
            'accumulated': d['account'].get('accumulated', 0),
        },
        'tickets': {'count': len(tickets)},
        'coupons': {'count': len(d['coupons'])},
        'prizes': {'count': len(prizes)},
        'note': '数据来自麦当劳官方 MCP 只读接口；如需完整可视化档案，请使用 mcd-archive 主仓库的 render 流程',
    }


@mcp.tool()
def get_tickets() -> list:
    """获取节气活动门票收藏线（麦当劳活动日历门票，按时间排序）"""
    d = _load_all()
    tickets = _tickets_of(d['prizes'])
    return sorted(tickets, key=lambda p: p['time'])


@mcp.tool()
def get_achievements() -> dict:
    """获取麦麦档案成就徽章：17 条规则，返回已解锁（含说明）与待解锁清单"""
    d = _load_all()
    tickets = _tickets_of(d['prizes'])
    unlocked, locked = evaluate_achievements(
        d['orders'], d['coupons'], tickets, d['account'], d['lottery'])
    return {
        'unlocked_count': len(unlocked),
        'total': len(unlocked) + len(locked),
        'unlocked': unlocked,
        'locked': locked,
    }


@mcp.tool()
def get_points_status() -> dict:
    """积分资产体检：可用/累计积分、抽奖活动状态、奖品与优惠券数量"""
    d = _load_all()
    account, lottery = d['account'], d['lottery']
    cost = lottery.get('cost_per_draw') or 0
    draws = int(account.get('available', 0) / cost) if cost else 0
    return {
        'available_point': account.get('available', 0),
        'accumulative_point': account.get('accumulated', 0),
        'expiring_point': account.get('expiring', 0),
        'lottery': {
            'activity': lottery.get('name', ''),
            'status': lottery.get('status', ''),
            'cost_per_draw': cost,
            'possible_draws': draws,
        },
        'prizes_count': len(d['prizes']),
        'coupons_count': len(d['coupons']),
    }


if __name__ == '__main__':
    mcp.run()  # stdio 传输，供 MCP 客户端接入

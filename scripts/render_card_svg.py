#!/usr/bin/env python3
"""SVG 分享卡生成器：profile.json → 单屏 SVG 海报（GitHub 原生渲染，无需浏览器截图）

用法:
    python3 render_card_svg.py [profile路径] [输出svg] [--name 昵称]
"""
import json
import os
import sys
from datetime import datetime

MEDAL_CHAR = {'solar': '藏', 'zero': '免', 'combo': '配', 'points': '分',
              'earlybird': '早', 'nooner': '午', 'night': '夜', 'loyal': '专',
              'merch': '周', 'big': '豪', 'coupon': '券', 'variety': '探',
              'span': '伴', 'lottery': '抽', 'veteran': '友', 'first': '初', 'cross': '跨'}
LV_TEXT = {'gold': '金牌成就', 'silver': '银牌成就', 'bronze': '铜牌成就'}
FONT = "-apple-system,'PingFang SC','Hiragino Sans GB','Microsoft YaHei',sans-serif"


def fmt(n):
    if n == int(n):
        return f'{int(n):,}'
    return f'{n:,.1f}'


def months_between(d1, d2):
    try:
        a = datetime.strptime(d1, '%Y-%m-%d')
        b = datetime.strptime(d2, '%Y-%m-%d')
        return max(1, int((b - a).days / 30.44))
    except Exception:
        return 0


def esc(s):
    return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def generate(profile, nickname='麦友'):
    ov, co, ac = profile['overview'], profile['collection'], profile['achievements']
    aset = profile.get('assets') or {}
    locked = profile.get('locked_achievements', [])

    t = co['tickets']
    mth = months_between(t[0]['time'], t[-1]['time']) if t else 0
    span_desc = f'{mth} 个多月' if mth else '这段时间'
    tickets_n = co['tickets_count']
    orders_n = ov['orders_count']
    badges_n = len(ac)
    badges_total = badges_n + len(locked)
    points = fmt(aset['points']['accumulated']) if aset.get('points') else '0'

    top = ac[:4] if ac else []
    while len(top) < 4:
        top.append({'id': 'first', 'name': '等待解锁', 'level': 'bronze'})

    hl_data = [(str(tickets_n), '张门票 · 一期不落'),
               (str(badges_n), '枚徽章 · 隐藏成就'),
               (points, '积分 · 历史累计')]

    arches = ('<path d="M12 104 Q12 16 40 16 Q68 16 68 104 M68 104 Q68 16 96 16 Q124 16 124 104" '
              'fill="none" stroke="#FFC72C" stroke-width="16" stroke-linecap="round"/>')

    hl_cards = ''
    for idx, (num, label) in enumerate(hl_data):
        x = 26 + idx * 268
        cx = x + 126
        hl_cards += f'''
  <rect x="{x}" y="398" width="252" height="110" rx="18" fill="#FFFFFF" stroke="#F2E3C0" stroke-width="2"/>
  <text x="{cx}" y="452" text-anchor="middle" font-family="{FONT}" font-size="42" font-weight="800" fill="#DA291C">{esc(num)}</text>
  <text x="{cx}" y="486" text-anchor="middle" font-family="{FONT}" font-size="14" fill="#6E6A60">{esc(label)}</text>'''

    badge_cards = ''
    for idx, b in enumerate(top):
        x = 26 + idx * 200
        cx = x + 93
        medal = MEDAL_CHAR.get(b.get('id'), '勋')
        badge_cards += f'''
  <rect x="{x}" y="524" width="186" height="118" rx="16" fill="#FFFFFF" stroke="#F0E7D6" stroke-width="1.5"/>
  <circle cx="{cx}" cy="562" r="24" fill="#FFC72C"/>
  <text x="{cx}" y="569" text-anchor="middle" font-family="{FONT}" font-size="20" font-weight="700" fill="#5A3E00">{esc(medal)}</text>
  <text x="{cx}" y="612" text-anchor="middle" font-family="{FONT}" font-size="15" font-weight="700" fill="#27251F">{esc(b.get('name',''))}</text>
  <text x="{cx}" y="632" text-anchor="middle" font-family="{FONT}" font-size="12" fill="#9A9484">{esc(LV_TEXT.get(b.get('level'), ''))}</text>'''

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 840 700" width="840" height="700">
<title>麦麦档案 · {esc(nickname)} 的麦当劳数据报告</title>
<defs>
  <pattern id="stripes" width="56" height="10" patternUnits="userSpaceOnUse">
    <rect width="28" height="10" fill="#DA291C"/>
    <rect x="28" width="28" height="10" fill="#FFC72C"/>
  </pattern>
</defs>
<rect x="0" y="0" width="840" height="700" rx="20" fill="#FBF5EA"/>
<rect x="26" y="26" width="788" height="10" rx="5" fill="url(#stripes)"/>
<rect x="26" y="52" width="788" height="330" rx="24" fill="#DA291C"/>
<text x="62" y="102" font-family="{FONT}" font-size="13" font-weight="700" letter-spacing="4" fill="#FFC72C">McD ARCHIVE · 麦当劳个人档案</text>
<text x="60" y="172" font-family="{FONT}" font-size="58" font-weight="800" letter-spacing="8" fill="#FFC72C">麦麦档案</text>
<text x="62" y="208" font-family="{FONT}" font-size="17" fill="#FFFFFF" opacity="0.95">{esc(nickname)} 的麦当劳数据报告</text>
<g transform="translate(658, 78) scale(1.05)">{arches}</g>
<rect x="62" y="248" width="620" height="54" rx="14" fill="#27251F"/>
<text x="84" y="281" font-family="{FONT}" font-size="17" font-weight="600" fill="#FFC72C">{esc(span_desc)} · <tspan fill="#FFFFFF" font-weight="800">{tickets_n} 张门票一期不落</tspan> · <tspan fill="#FFFFFF">{orders_n} 顿饭拿下 {badges_n} 枚徽章</tspan></text>
<text x="62" y="344" font-family="{FONT}" font-size="12.5" fill="#FFFFFF" opacity="0.72">档案生成于 {datetime.now().strftime('%Y-%m-%d')} · 数据来自麦当劳官方 MCP</text>{hl_cards}{badge_cards}
<text x="420" y="676" text-anchor="middle" font-family="{FONT}" font-size="12.5" fill="#9A9484">已解锁 {badges_n} / {badges_total} 枚徽章 · 数据来自麦当劳官方 MCP · 非官方产品</text>
</svg>'''
    return svg


def main():
    base = os.path.dirname(os.path.abspath(__file__))
    argv = sys.argv[1:]
    nickname = '麦友'
    positional = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == '--name' and i + 1 < len(argv):
            nickname = argv[i + 1]
            i += 2
            continue
        positional.append(a)
        i += 1
    profile_path = positional[0] if positional else os.path.join(base, '..', 'data', 'profile.json')
    out = positional[1] if len(positional) > 1 else os.path.join(base, '..', 'data', 'card.svg')
    with open(profile_path, encoding='utf-8') as f:
        profile = json.load(f)
    svg = generate(profile, nickname)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, 'w', encoding='utf-8') as f:
        f.write(svg)
    print(f'OK [svg] → {out}  ({len(svg)} chars)')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""渲染器：profile.json → 麦麦档案 HTML 报告（单文件，截图即传播）

用法:
    python3 render.py [profile路径] [输出html] [--name 昵称]
"""
import json
import os
import sys
from datetime import datetime


ARCHES_SVG = '''<svg class="arches" viewBox="0 0 136 110" width="104" aria-hidden="true">
<path d="M12 104 Q12 16 40 16 Q68 16 68 104 M68 104 Q68 16 96 16 Q124 16 124 104"
 fill="none" stroke="#FFC72C" stroke-width="16" stroke-linecap="round"/></svg>'''

CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: #FBF5EA; font-family: -apple-system, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif; color: #27251F; line-height: 1.65; padding: 22px 12px 48px; }
.report { max-width: 780px; margin: 0 auto; }

.stripes { height: 10px; border-radius: 6px; background: repeating-linear-gradient(90deg, #DA291C 0 28px, #FFC72C 28px 56px); margin-bottom: 18px; }

.cover { background: #DA291C; border-radius: 26px; padding: 46px 44px 42px; color: #fff; }
.cover-top { display: flex; justify-content: space-between; align-items: flex-start; gap: 20px; }
.cover-tag { font-size: 12px; letter-spacing: 4px; color: #FFC72C; font-weight: 700; margin-bottom: 16px; }
.cover h1 { font-size: 56px; letter-spacing: 8px; color: #FFC72C; font-weight: 800; line-height: 1.1; margin-bottom: 12px; }
.cover-sub { font-size: 16px; opacity: .95; }
.cover-line { margin-top: 30px; font-size: 17px; font-weight: 600; background: #27251F; color: #FFC72C; padding: 14px 18px; border-radius: 14px; max-width: 560px; }
.cover-line b { color: #fff; }
.cover-date { font-size: 12px; opacity: .72; margin-top: 20px; }

section { margin-top: 28px; }
h2 { font-size: 20px; margin-bottom: 14px; display: flex; align-items: center; gap: 10px; }
h2::before { content: ""; width: 12px; height: 12px; background: #DA291C; border-radius: 4px; }
h2 .hint { font-size: 12px; color: #8A8578; font-weight: 400; }

.highlights { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.hl { background: #fff; border: 2px solid #F2E3C0; border-radius: 20px; padding: 20px 20px 16px; text-align: center; }
.hl b { display: block; font-size: 40px; color: #DA291C; font-weight: 800; line-height: 1.15; }
.hl span { font-size: 13px; color: #6E6A60; }
.hl-note { margin-top: 10px; font-size: 12.5px; color: #8A8578; text-align: center; }

.card { background: #fff; border-radius: 18px; padding: 22px 24px; border: 1.5px solid #F0E7D6; }
.tags { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 14px; }
.tag { background: #FFF3D6; border: 2px solid #FFC72C; color: #7A5B00; font-weight: 700; font-size: 14.5px; padding: 7px 18px; border-radius: 999px; }
.persona-copy { font-size: 14.5px; color: #4A463D; }

.g-ach { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.ach { background: #fff; border-radius: 18px; padding: 18px 20px; display: flex; gap: 16px; align-items: center; border: 1.5px solid #F0E7D6; }
.ach .medal { width: 52px; height: 52px; min-width: 52px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 24px; }
.gold .medal { background: #FFC72C; }
.silver .medal { background: #E8E4DA; }
.bronze .medal { background: #F0D5B8; }
.ach b { font-size: 15.5px; display: block; margin-bottom: 3px; }
.ach p { font-size: 12.5px; color: #6E6A60; }
.ach .lv { font-size: 11px; color: #B08A2E; font-weight: 700; letter-spacing: 2px; }
.silver .lv { color: #9A9484; }
.bronze .lv { color: #B47B4C; }
.locked-line { font-size: 12.5px; color: #9A9484; margin-top: 12px; padding-left: 4px; }

.tickets-wrap { background: #fff; border-radius: 20px; padding: 22px 24px; border: 1.5px solid #F0E7D6; }
.tickets-meta { font-size: 13px; color: #6E6A60; margin-bottom: 16px; }
.tickets-meta b { color: #DA291C; font-size: 15px; }
.tickets { display: flex; flex-wrap: wrap; gap: 9px; }
.ticket { display: inline-flex; align-items: center; gap: 8px; background: #FFFBF1; border: 1.5px dashed #E8C97A; border-radius: 12px; padding: 7px 14px; font-size: 13.5px; font-weight: 600; color: #5A4A20; }
.ticket i { width: 9px; height: 9px; background: #FFC72C; border-radius: 50%; }
.ticket small { color: #A89C7C; font-size: 11px; font-weight: 400; }

.assets { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.asset-card { background: #fff; border-radius: 18px; padding: 20px 22px; border: 1.5px solid #F0E7D6; }
.asset-card h3 { font-size: 13.5px; color: #6E6A60; font-weight: 700; margin-bottom: 10px; letter-spacing: 1px; }
.asset-big { font-size: 32px; font-weight: 800; color: #27251F; }
.asset-big small { font-size: 13.5px; color: #6E6A60; font-weight: 400; }
.asset-sub { font-size: 12.5px; color: #6E6A60; margin-top: 6px; }
.asset-sub .warn { color: #DA291C; font-weight: 700; }
.milestone { grid-column: 1 / -1; }
.bar { height: 16px; background: #F3ECDD; border-radius: 999px; overflow: hidden; margin: 12px 0 8px; }
.bar i { display: block; height: 100%; border-radius: 999px; background: repeating-linear-gradient(90deg, #DA291C 0 14px, #E8473B 14px 28px); }
.redeem { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 4px; }
.redeem span { background: #FFF3D6; border-radius: 10px; padding: 6px 12px; font-size: 13px; font-weight: 600; color: #7A5B00; }

footer { margin-top: 34px; text-align: center; font-size: 12px; color: #9A9484; line-height: 2; }
@media (max-width: 640px) {
  .highlights { grid-template-columns: 1fr; }
  .hl { padding: 16px 18px 12px; }
  .hl b { font-size: 32px; }
  .g-ach { grid-template-columns: 1fr; }
  .assets { grid-template-columns: 1fr; }
  .cover { padding: 34px 26px 30px; }
  .cover h1 { font-size: 40px; letter-spacing: 5px; }
  .arches { display: none; }
}
"""

ACH_ICONS = {'solar': '🗓️', 'zero': '🎯', 'earlybird': '🌅', 'combo': '🍔',
             'cross': '📍', 'merch': '🎧', 'points': '💎',
             'first': '✨', 'nooner': '☀️', 'night': '🌙', 'loyal': '🏠',
             'big': '💸', 'coupon': '🎫', 'variety': '🧭', 'span': '⏳',
             'lottery': '🎰', 'veteran': '🤝'}
LV_TEXT = {'gold': '金', 'silver': '银', 'bronze': '铜'}


def fmt(n):
    if n == int(n):
        return f'{int(n):,}'
    return f'{n:,.1f}'


def months_between(d1, d2):
    try:
        a = datetime.strptime(d1, '%Y-%m-%d')
        b = datetime.strptime(d2, '%Y-%m-%d')
        days = (b - a).days
        return max(1, int(days / 30.44))
    except Exception:
        return 0


def render(profile, nickname='麦友', anonymize=False):
    m, ov, hb = profile['meta'], profile['overview'], profile['habits']
    co, ac, aset = profile['collection'], profile['achievements'], profile['assets']
    locked = profile.get('locked_achievements', [])
    tags = profile['persona']['tags']
    store_display = '你的常去门店' if anonymize else hb['fav_store']

    # 封面金句（自适应：有门票讲收藏线，没门票讲引导）
    t = co['tickets']
    if t:
        mth = months_between(t[0]['time'], t[-1]['time'])
        span_desc = f'{mth} 个多月' if mth else '这段时间'
        story = (f"{span_desc} · <b>{co['tickets_count']} 张门票一期不落</b> · "
                 f"{ov['orders_count']} 顿饭拿下 <b>{len(ac)} 枚徽章</b>")
    elif ov['orders_count']:
        story = f"档案已建立 · {ov['orders_count']} 顿饭拿下 <b>{len(ac)} 枚徽章</b> · 收藏线等你的第一张门票"
    else:
        story = "档案刚刚建立 · 去麦当劳吃一顿，回来就有故事了"

    # 三高光（自适应挑强项，空数据用占位）
    cand = []
    if co['tickets_count']:
        cand.append((str(co['tickets_count']), '张门票 · 一期不落'))
    if ac:
        cand.append((str(len(ac)), '枚徽章 · 隐藏成就'))
    if aset and aset['points']['accumulated']:
        cand.append((fmt(aset['points']['accumulated']), '积分 · 历史累计'))
    if ov['orders_count']:
        cand.append((str(ov['orders_count']), '笔订单 · 有据可查'))
    if aset and aset['coupons_count']:
        cand.append((str(aset['coupons_count']), '张待用券'))
    while len(cand) < 3:
        cand.append(('—', '等你解锁'))
    hls = cand[:3]
    hl_html = ''.join(f'<div class="hl"><b>{v}</b><span>{k}</span></div>' for v, k in hls)

    parts = []
    if ov['orders_count']:
        parts.append(f"{ov['orders_count']} 笔订单")
    if ov['stores_count']:
        parts.append(f"{ov['stores_count']} 家门店")
    if ov['zero_orders']:
        parts.append(f"{ov['zero_orders']} 次免单")
    if ov['total_spent']:
        parts.append(f"¥{fmt(ov['total_spent'])} 有记录的消费")
    hl_note = ('还有：' + ' · '.join(parts)) if parts else '这还是一张空白档案，去创造第一笔记录吧'

    tag_html = ''.join(f'<span class="tag">{x}</span>' for x in tags)
    persona_copy = (f"数据说：你偏爱在上午出没，习惯用组合拳点单；"
                    f"收藏从不落下一期，钱包则被券管得服服帖帖。"
                    f"主门店是「{store_display}」（{hb['fav_store_count']} 单）。")

    ach_html = ''.join(
        f'<div class="ach {a["level"]}"><div class="medal">{ACH_ICONS.get(a["id"], "🏅")}</div>'
        f'<div><span class="lv">{LV_TEXT.get(a["level"], "")}</span><b>{a["name"]}</b><p>{a["desc"]}</p></div></div>'
        for a in ac)
    if not ach_html:
        ach_html = ('<div class="ach bronze"><div class="medal">🌟</div>'
                    '<div><span class="lv">铜</span><b>档案探员</b><p>第一顿麦当劳下肚，成就就会开始解锁</p></div></div>')
    ach_total = len(ac) + len(locked)
    locked_html = ''
    if locked:
        names = ' · '.join(x['name'] for x in locked)
        locked_html = f'<p class="locked-line">待解锁 {len(locked)} 枚：{names}</p>'

    if co['tickets']:
        ticket_html = ''.join(
            f'<span class="ticket"><i></i>{x["name"]}<small>{x["time"]}</small></span>'
            for x in co['tickets'])
        tickets_inner = (f'<p class="tickets-meta">共 <b>{co["tickets_count"]}</b> 张 · {co["span"]} · 一期不落</p>'
                         f'<div class="tickets">{ticket_html}</div>')
    else:
        tickets_inner = '<p class="tickets-meta">收藏线还在等待开始 —— 集齐第一张活动门票，它就会出现在这里。</p>'

    assets_html = ''
    if aset and (aset['points']['accumulated'] or aset['coupons_count'] or aset['affordable_draws']):
        p = aset['points']
        pct = min(100, round(p['available'] / aset['next_milestone']['points'] * 100, 1)) if aset.get('next_milestone') else 0
        redeem_html = ''.join(f'<span>{r["name"]} · {fmt(r["points"])} 分</span>' for r in aset.get('redeemable_now', []))
        redeem_section = ''
        if redeem_html:
            redeem_section = f'''
  <section>
    <h2>当前可兑换 <span class="hint">现有积分即可拿下</span></h2>
    <div class="card"><div class="redeem">{redeem_html}</div></div>
  </section>'''
        milestone_html = ''
        if aset.get('next_milestone'):
            milestone_html = f"""
      <div class="asset-card milestone">
        <h3>下一个里程碑</h3>
        <div class="asset-big">{aset['next_milestone']['name']} <small>需 {fmt(aset['next_milestone']['points'])} 分</small></div>
        <div class="bar"><i style="width:{pct}%"></i></div>
        <div class="asset-sub">当前 {fmt(p['available'])} 分（{pct}%）· 还差 <b>{fmt(aset['milestone_gap'])}</b> 分</div>
      </div>"""
        warn = f'<div class="asset-sub"><span class="warn">即将过期 {fmt(p["expiring"])} 分</span> · 记得尽快用掉</div>' if p.get('expiring') else ''
        assets_html = f"""
  <section>
    <h2>资产体检 <span class="hint">积分 · 券 · 抽奖</span></h2>
    <div class="assets">
      <div class="asset-card">
        <h3>积分资产</h3>
        <div class="asset-big">{fmt(p['available'])} <small>可用积分</small></div>
        <div class="asset-sub">历史累计 {fmt(p['accumulated'])} · 已花 {fmt(p['used'])}</div>
        {warn}
      </div>
      <div class="asset-card">
        <h3>麦麦积分抽奖</h3>
        <div class="asset-big">{aset['affordable_draws']} <small>次可抽</small></div>
        <div class="asset-sub">{fmt(aset['lottery']['cost_per_draw'])} 分/次 · {aset['lottery']['prizes_count']} 种奖品</div>
      </div>
      <div class="asset-card">
        <h3>券包</h3>
        <div class="asset-big">{aset['coupons_count']} <small>张待用券</small></div>
        <div class="asset-sub">到期前记得用掉</div>
      </div>
      {milestone_html}
    </div>
  </section>{redeem_section}"""

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>麦麦档案 · {nickname}</title>
<style>{CSS}</style>
</head>
<body>
<div class="report">
  <div class="stripes"></div>
  <header class="cover">
    <div class="cover-top">
      <div>
        <div class="cover-tag">McD ARCHIVE · 麦当劳个人档案</div>
        <h1>麦麦档案</h1>
        <p class="cover-sub">{nickname} 的麦当劳数据报告</p>
      </div>
      {ARCHES_SVG}
    </div>
    <p class="cover-line">{story}</p>
    <p class="cover-date">档案生成于 {m['generated_at']} · 数据来自麦当劳官方 MCP</p>
  </header>

  <section>
    <div class="highlights">{hl_html}</div>
    <p class="hl-note">{hl_note}</p>
  </section>

  <section>
    <h2>麦麦人设</h2>
    <div class="card">
      <div class="tags">{tag_html}</div>
      <p class="persona-copy">{persona_copy}</p>
    </div>
  </section>

  <section>
    <h2>隐藏成就 <span class="hint">已解锁 {len(ac)} / {ach_total} 枚</span></h2>
    <div class="g-ach">{ach_html}</div>
    {locked_html}
  </section>

  <section>
    <h2>数字收藏馆 <span class="hint">门票收藏线</span></h2>
    <div class="tickets-wrap">
      {tickets_inner}
    </div>
  </section>

  {assets_html}

  <footer>
    本档案由「麦麦档案」Skill 基于麦当劳 MCP 数据生成<br>
    非麦当劳官方产品 · 数据仅存于本地 · {m['generated_at']}
  </footer>
</div>
</body>
</html>"""
    return html


CARD_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: #FBF5EA; font-family: -apple-system, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif; color: #27251F; padding: 26px; }
.card { width: 780px; margin: 0 auto; }
.stripes { height: 10px; border-radius: 6px; background: repeating-linear-gradient(90deg, #DA291C 0 28px, #FFC72C 28px 56px); margin-bottom: 16px; }
.cover { background: #DA291C; border-radius: 24px; padding: 32px 34px 28px; color: #fff; }
.cover-top { display: flex; justify-content: space-between; align-items: center; gap: 16px; }
.cover-tag { font-size: 11px; letter-spacing: 4px; color: #FFC72C; font-weight: 700; margin-bottom: 10px; }
.cover h1 { font-size: 44px; letter-spacing: 7px; color: #FFC72C; font-weight: 800; line-height: 1.1; margin-bottom: 8px; }
.cover-sub { font-size: 14px; opacity: .95; }
.cover-line { margin-top: 18px; font-size: 15px; font-weight: 600; background: #27251F; color: #FFC72C; padding: 11px 15px; border-radius: 12px; }
.cover-line b { color: #fff; }
.highlights { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-top: 14px; }
.hl { background: #fff; border: 2px solid #F2E3C0; border-radius: 18px; padding: 16px 12px 12px; text-align: center; }
.hl b { display: block; font-size: 34px; color: #DA291C; font-weight: 800; line-height: 1.15; }
.hl span { font-size: 12px; color: #6E6A60; }
.badges { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-top: 14px; }
.badge { background: #fff; border: 1.5px solid #F0E7D6; border-radius: 14px; padding: 12px 10px; text-align: center; }
.badge .m { width: 44px; height: 44px; border-radius: 50%; margin: 0 auto 8px; display: flex; align-items: center; justify-content: center; font-size: 21px; }
.badge .m.gold { background: #FFC72C; }
.badge .m.silver { background: #E8E4DA; }
.badge .m.bronze { background: #F0D5B8; }
.badge b { font-size: 13px; display: block; margin-bottom: 2px; }
.badge span { font-size: 11px; color: #9A9484; }
.footline { margin-top: 14px; text-align: center; font-size: 12px; color: #9A9484; }
"""


def render_card(profile, nickname='麦友'):
    """分享卡：单屏海报版式（README 主图 / 转发用）"""
    ov = profile['overview']
    co, ac = profile['collection'], profile['achievements']
    aset = profile.get('assets') or {}
    locked = profile.get('locked_achievements', [])

    t = co['tickets']
    if t:
        mth = months_between(t[0]['time'], t[-1]['time'])
        story = (f"{mth} 个多月 · <b>{co['tickets_count']} 张门票一期不落</b> · "
                 f"{ov['orders_count']} 顿饭拿下 <b>{len(ac)} 枚徽章</b>")
    elif ov['orders_count']:
        story = f"档案已建立 · {ov['orders_count']} 顿饭拿下 <b>{len(ac)} 枚徽章</b>"
    else:
        story = "档案刚刚建立 · 去麦当劳吃一顿，回来就有故事了"

    cand = []
    if co['tickets_count']:
        cand.append((str(co['tickets_count']), '张门票 · 一期不落'))
    if ac:
        cand.append((str(len(ac)), '枚徽章 · 隐藏成就'))
    if aset.get('points', {}).get('accumulated'):
        cand.append((fmt(aset['points']['accumulated']), '积分 · 历史累计'))
    if ov['orders_count']:
        cand.append((str(ov['orders_count']), '笔订单 · 有据可查'))
    while len(cand) < 3:
        cand.append(('—', '等你解锁'))
    hl_html = ''.join(f'<div class="hl"><b>{v}</b><span>{k}</span></div>' for v, k in cand[:3])

    top = ac[:4] if ac else [{'id': 'first', 'name': '等待解锁', 'level': 'bronze'}]
    badge_html = ''.join(
        f'<div class="badge"><div class="m {x["level"]}">{ACH_ICONS.get(x["id"], "🏅")}</div>'
        f'<b>{x["name"]}</b><span>{LV_TEXT.get(x["level"], "")}牌成就</span></div>'
        for x in top)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>麦麦档案分享卡 · {nickname}</title>
<style>{CARD_CSS}</style>
</head>
<body>
<div class="card">
  <div class="stripes"></div>
  <header class="cover">
    <div class="cover-top">
      <div>
        <div class="cover-tag">McD ARCHIVE · 麦当劳个人档案</div>
        <h1>麦麦档案</h1>
        <p class="cover-sub">{nickname} 的麦当劳数据报告</p>
      </div>
      {ARCHES_SVG}
    </div>
    <p class="cover-line">{story}</p>
  </header>
  <div class="highlights">{hl_html}</div>
  <div class="badges">{badge_html}</div>
  <p class="footline">已解锁 {len(ac)} / {len(ac) + len(locked)} 枚徽章 · 数据来自麦当劳官方 MCP · 非官方产品</p>
</div>
</body>
</html>"""


def main():
    base = os.path.dirname(os.path.abspath(__file__))
    argv = sys.argv[1:]
    nickname = '麦友'
    mode = 'report'
    anonymize = False
    positional = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == '--name' and i + 1 < len(argv):
            nickname = argv[i + 1]
            i += 2
            continue
        if a == '--mode' and i + 1 < len(argv):
            mode = argv[i + 1]
            i += 2
            continue
        if a == '--anon':
            anonymize = True
            i += 1
            continue
        positional.append(a)
        i += 1
    default_out = 'report_card.html' if mode == 'card' else 'report.html'
    profile_path = positional[0] if positional else os.path.join(base, '..', 'data', 'profile.json')
    out = positional[1] if len(positional) > 1 else os.path.join(base, '..', 'data', default_out)
    with open(profile_path, encoding='utf-8') as f:
        profile = json.load(f)
    html = render_card(profile, nickname) if mode == 'card' else render(profile, nickname, anonymize)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'OK [{mode}{" anon" if anonymize else ""}] → {out}  ({len(html)} chars)')


if __name__ == '__main__':
    main()

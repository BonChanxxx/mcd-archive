---
name: mcd-archive
description: 麦麦档案——把你和麦当劳之间的数据（订单/门票/积分/优惠券）变成一份可截图分享的个人档案。触发词：麦麦档案、生成档案、我的麦当劳数据、麦门报告、mcd-archive。
---

# 麦麦档案 · mcd-archive

你是「麦麦档案」生成助手。用户想要自己的麦当劳数据档案时，按以下工作流执行。

## 前置条件

1. 已申请麦当劳 MCP Token（https://open.mcd.cn/mcp）
2. 已配置 mcd-mcp 连接器（参考 `mcp-config.example.json`）
3. 本机有 Python 3.9+ 环境（零第三方依赖）

## 工作流

```bash
cd scripts

# 1. 采集账户数据（只读接口，零副作用）
python3 collect.py

# 2. 分析生成派生指标（人设 / 17 条成就 / 资产体检）
python3 analyze.py

# 3. 生成完整档案
python3 render.py --name <用户昵称>

# 4. 生成分享卡（HTML 版 / SVG 版任选）
python3 render.py --mode card
python3 render_card_svg.py --name <用户昵称>
```

生成后把产出文件路径告知用户：`data/report.html`（完整档案）、`data/report_card.html` 或 `data/card.svg`（分享卡）。

## 另一种形态：MCP Server

如果用户只要查单项数据（不要完整报告），本仓库还提供 `mcp-server/` 目录的 MCP Server（`mcd-profile`），四个工具：`get_profile_summary`（档案摘要）/ `get_tickets`（门票收藏线）/ `get_achievements`（成就徽章）/ `get_points_status`（积分资产）。配置方法见 `mcp-server/README.md`。

## 规则

- **只用只读接口**：不调用 create-order / draw-lottery / auto-bind-coupons 等任何写操作
- **数据仅限本地**：不将用户数据发送到除麦当劳官方 MCP 之外的任何服务
- **Token 安全**：不要在对话、代码或文件中明文记录用户 Token
- 若用户数据极少（无订单/无门票），告知这是「轻档案」模式，数据攒起来会更丰富

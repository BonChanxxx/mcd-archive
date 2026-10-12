# MCP 集成说明（MCP_INTEGRATION.md）

## 一、使用的麦当劳 MCP Server

| 项 | 内容 |
|---|---|
| 名称 | 麦当劳中国 MCP Server（mcd-mcp） |
| 地址 | `https://mcp.mcd.cn` |
| 协议 | Streamable HTTP |
| 认证 | `Authorization: Bearer <MCP Token>`（在 https://open.mcd.cn/mcp 申请） |
| 官方工具总数 | 35 个（截至 2026-10-09） |

## 二、本项目实际调用的 Tool 清单（全部为只读接口）

| Tool | 用途 | 调用模块 | 产出位置 |
|---|---|---|---|
| `order-list` | 读取近期订单（商品/金额/门店/时间） | `scripts/collect.py` | 数字一览 / 麦麦人设 / 成就判定 |
| `query-my-account` | 积分账户（可用/累计/已用/将过期） | `scripts/collect.py` | 资产体检 / 积分大亨成就 |
| `query-my-prizes` | 奖品与活动门票记录（翻页拉全） | `scripts/collect.py` | 数字收藏馆 |
| `query-my-coupons` | 我的优惠券列表 | `scripts/collect.py` | 资产体检 / 券包富人成就 |
| `available-coupons` | 麦麦省可领券 | `scripts/collect.py` | 数据储备（扩展位） |
| `query-lottery-info` | 积分抽奖活动（状态/消耗/奖品池） | `scripts/collect.py` | 资产体检 / 抽奖大户成就 |
| `campaign-calendar` | 月度活动日历 | `scripts/collect.py` | 数据储备 / 活动背景 |
| `mall-points-products` | 积分商城商品（兑换里程碑） | `scripts/collect.py` | 资产体检（里程碑进度条） |
| `list-nutrition-foods` | 餐品营养库（160 项） | `scripts/collect.py` | 数据储备（v2 扩展位） |
| `now-time-info` | 服务器时间（数据快照时间戳） | `scripts/collect.py` | 档案生成时间 |

> 说明：本项目对麦当劳 MCP 的使用方式是**「只读取数 + 本地生成」**——不调用任何写接口（不下单、不扣分、不领券、不抽奖），对用户账户零副作用。

## 三、调用流程

```
用户在 open.mcd.cn/mcp 申请 Token
          │
          ▼
配置 MCP 客户端（mcp-config.example.json，仅环境变量占位符）
          │
          ▼
scripts/collect.py ──► 依次调用 10 个只读 Tool ──► data/raw/*.json
          │
          ▼
scripts/analyze.py ──► 派生指标计算 ──► profile.json
        （麦麦人设 / 17 条成就判定 / 资产体检 / 门票收藏线）
          │
          ▼
scripts/render.py ──► report.html（完整档案）
scripts/render.py --mode card ──► report_card.html（分享卡）
scripts/render_card_svg.py ──► card.svg（免截图版分享卡）
```

## 四、业务价值

1. **数据 → 叙事**：把麦当劳账户中沉睡的订单、门票、积分数据，转化为有情绪价值与分享价值的个人档案——这是「只读数据」的创造性用法
2. **零侵入 & 零成本**：全部只读接口，不消耗用户任何积分/权益；零第三方依赖，代码完全可审计
3. **真实可信**：档案中的所有数字均来自官方接口实时数据，无模拟、无估算
4. **可扩展**：营养库、活动日历、菜单等数据已完成采集与验证，为后续版本（营养分析、活动推荐）预留扩展位

## 五、安全与合规

- **Token 不入库**：Token 通过环境变量 `MCD_TOKEN` 或本地安全存储（macOS 钥匙串）读取；本仓库配置文件仅含环境变量占位符
- **数据不出本地**：采集数据仅存于本地 `data/` 目录（已 gitignore），不上传任何第三方服务
- **限流合规**：采集请求间隔 250ms，远低于官方 600 次/分钟限制

## 六、附：本项目自身的 MCP Server 形态

除上述「消费官方 MCP」的定位外，本项目还以 **MCP Server 生产者**身份发布：`mcp-server/` 目录提供 `mcd-profile` Server（档案摘要 / 门票收藏线 / 成就徽章 / 积分资产四个只读工具），底层仍调用本文所列的麦当劳官方 MCP 只读接口。配置方式见 `mcp-server/README.md`。

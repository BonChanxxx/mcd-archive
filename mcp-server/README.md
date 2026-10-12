# mcd-profile · 麦当劳档案 MCP Server

「麦麦档案」（[mcd-archive](https://github.com/BonChanxxx/mcd-archive)）的 MCP Server 形态：基于**麦当劳官方 MCP**（https://mcp.mcd.cn）的轻量档案查询服务，把账号数据以标准 MCP 工具暴露给任何 MCP 客户端（Claude Desktop、WorkBuddy、Cherry Studio 等）。

## 工具列表

| 工具 | 说明 |
|---|---|
| `get_profile_summary` | 档案摘要：订单数 / 门店数 / 总消费 / 积分 / 门票 / 券 / 奖品总览 |
| `get_tickets` | 节气活动门票收藏线（按时间排序） |
| `get_achievements` | 成就徽章：17 条规则，返回已解锁（含说明）+ 待解锁清单 |
| `get_points_status` | 积分资产体检：可用 / 累计积分、抽奖活动状态、奖品与券数量 |

## 安装

```bash
pip install -r requirements.txt   # 仅依赖 mcp 官方 SDK
```

底层数据访问复用主仓库的零依赖客户端 `../scripts/mcd_client.py`（纯标准库实现）。

## 配置（MCP 客户端）

```json
{
  "mcpServers": {
    "mcd-profile": {
      "command": "python3",
      "args": ["<本仓库绝对路径>/mcp-server/server.py"],
      "env": { "MCD_TOKEN": "<你的麦当劳 MCP Token>" }
    }
  }
}
```

Token 申请：打开 https://open.mcd.cn/mcp ，手机号登录 → 控制台 → 激活 → 复制。

配好后对 AI 助手说「看看我的麦当劳档案」即可触发。

## 数据安全

- 全部走麦当劳官方 MCP **只读接口**：不扣分、不下单、不领券
- Token 仅从环境变量 `MCD_TOKEN` 读取（stdio 模式由客户端注入）
- 本服务不存储、不上传任何账号数据；查询结果仅返回给调用方

## 与主仓库的关系

| 组件 | 定位 |
|---|---|
| `mcp-server/server.py` | 实时查询型 MCP Server（本目录） |
| `scripts/` 工具链 | 一次性生成完整可视化档案 + 分享卡 |

两者数据源一致（官方 MCP）、成就规则一致（17 条），按场景选用。

---

*麦当劳程序员创意开发大赛参赛作品 · 非麦当劳官方产品 · MIT License*

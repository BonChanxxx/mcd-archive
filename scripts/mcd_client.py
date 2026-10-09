#!/usr/bin/env python3
"""麦当劳 MCP 客户端 — 极简 Streamable HTTP 实现（零第三方依赖）

Token 读取顺序: 环境变量 MCD_TOKEN → macOS 钥匙串(service=mcd-mcp-token) → /tmp/mcd_token.txt → ~/.mcd_token

用法:
    from mcd_client import McdMcpClient
    client = McdMcpClient()
    data = client.call_data('query-my-account')
"""
import json
import os
import subprocess
import sys
import urllib.request
import urllib.error

DEFAULT_URL = 'https://mcp.mcd.cn'


class McdMcpClient:
    def __init__(self, token=None, url=DEFAULT_URL):
        self.url = url
        self.token = token or self._load_token()

    @staticmethod
    def _load_token():
        t = os.environ.get('MCD_TOKEN')
        if t:
            return t.strip()
        if sys.platform == 'darwin':
            try:
                out = subprocess.run(
                    ['security', 'find-generic-password', '-s', 'mcd-mcp-token', '-w'],
                    capture_output=True, text=True, timeout=5)
                if out.returncode == 0 and out.stdout.strip():
                    return out.stdout.strip()
            except Exception:
                pass
        for p in ('/tmp/mcd_token.txt', os.path.expanduser('~/.mcd_token')):
            if os.path.exists(p):
                with open(p) as f:
                    return f.read().strip()
        raise RuntimeError('未找到 MCP Token：请设置环境变量 MCD_TOKEN，或存入 macOS 钥匙串（service=mcd-mcp-token）')

    def _rpc(self, method, params=None):
        body = {'jsonrpc': '2.0', 'id': 1, 'method': method}
        if params is not None:
            body['params'] = params
        req = urllib.request.Request(self.url, data=json.dumps(body).encode('utf-8'), method='POST')
        req.add_header('Authorization', 'Bearer ' + self.token)
        req.add_header('Content-Type', 'application/json')
        req.add_header('Accept', 'application/json, text/event-stream')
        resp = urllib.request.urlopen(req, timeout=90)
        raw = resp.read().decode('utf-8', 'replace')
        ct = resp.headers.get('Content-Type', '')
        if 'text/event-stream' in ct:
            for line in raw.split('\n'):
                line = line.strip()
                if line.startswith('data:'):
                    payload = line[5:].strip()
                    if payload:
                        return json.loads(payload)
            return None
        return json.loads(raw)

    def call(self, tool, args=None):
        """调用工具，返回完整 JSON-RPC 响应"""
        return self._rpc('tools/call', {'name': tool, 'arguments': args or {}})

    def call_data(self, tool, args=None):
        """调用工具并返回 structuredContent（无则返回文本内容）"""
        r = self.call(tool, args)
        if not r or 'result' not in r:
            raise RuntimeError(f'{tool} 调用失败: {json.dumps(r, ensure_ascii=False)[:200]}')
        res = r['result']
        if res.get('isError'):
            raise RuntimeError(f'{tool} 返回错误: {json.dumps(res, ensure_ascii=False)[:200]}')
        sc = res.get('structuredContent')
        if sc is not None:
            return sc
        texts = [c.get('text', '') for c in res.get('content', []) if c.get('type') == 'text']
        return '\n'.join(texts)

    def list_tools(self):
        r = self._rpc('tools/list')
        return r['result']['tools']


if __name__ == '__main__':
    c = McdMcpClient()
    tools = c.list_tools()
    print(f'OK — {len(tools)} 个工具可用')
    t = c.call_data('now-time-info')
    print('服务器时间:', t.get('datetime') if isinstance(t, dict) else t)

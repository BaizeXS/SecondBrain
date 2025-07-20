#!/usr/bin/env python3
"""简单的测试服务器 - 提供 API 测试界面"""

import http.server
import socketserver
import os

PORT = 8080

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # 添加 CORS 头
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_GET(self):
        if self.path == '/':
            # 默认提供简单测试页面
            self.path = '/simple_api_test.html'
        return super().do_GET()

os.chdir(os.path.dirname(os.path.abspath(__file__)))

print(f"🌐 启动简单测试服务器...")
print(f"📍 访问地址: http://localhost:{PORT}")
print(f"📝 提供页面:")
print(f"   - 简单测试界面: http://localhost:{PORT}/simple_api_test.html")
print(f"   - 增强测试界面: http://localhost:{PORT}/test_web_interface_enhanced.html")
print(f"   - 基础测试界面: http://localhost:{PORT}/test_web_interface.html")
print(f"\n按 Ctrl+C 停止服务器")

with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
    httpd.serve_forever()
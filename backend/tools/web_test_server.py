#!/usr/bin/env python3
"""简单的 HTTP 服务器，用于提供测试页面"""

import http.server
import os
import socketserver
import sys
import webbrowser

PORT = 8080


class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # 添加 CORS 头
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()


os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 检查命令行参数
enhanced = '--enhanced' in sys.argv or '-e' in sys.argv

# 选择界面文件
if enhanced:
    interface_file = 'test_web_interface_enhanced.html'
    print("✨ 使用增强版测试界面")
else:
    interface_file = 'test_web_interface.html'
    print("💡 提示: 使用 --enhanced 或 -e 参数启动增强版界面")

with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
    print("🌐 测试服务器已启动")
    print(f"📍 请在浏览器中访问: http://localhost:{PORT}/{interface_file}")
    print("✋ 按 Ctrl+C 停止服务器")
    
    # 自动打开浏览器
    try:
        webbrowser.open(f'http://localhost:{PORT}/{interface_file}')
    except:
        pass
    
    httpd.serve_forever()
#!/usr/bin/env python3
"""
Servidor simples para testar o HTML sem problemas de CORS
"""
import http.server
import socketserver
import os

PORT = 8001
DIRECTORY = "/Users/levilaell/Desktop/finance_hub"

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

print(f"Servidor rodando em http://localhost:{PORT}")
print(f"Acesse: http://localhost:{PORT}/test_frontend_error.html")
print("Pressione Ctrl+C para parar")

with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor parado")
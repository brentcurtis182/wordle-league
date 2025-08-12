#!/usr/bin/env python3
import http.server
import socketserver
import os
import sys

# Use port 7777 which is less likely to be in use
PORT = 7777

# Get directory to serve
serve_dir = "website_export"
if len(sys.argv) > 1:
    serve_dir = sys.argv[1]

# Change to the directory we want to serve
os.chdir(serve_dir)

# Create the handler
handler = http.server.SimpleHTTPRequestHandler

# Create the server
with socketserver.TCPServer(("", PORT), handler) as httpd:
    print(f"Serving files from {os.path.abspath(os.curdir)} at http://localhost:{PORT}")
    httpd.serve_forever()

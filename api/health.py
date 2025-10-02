import json
import sys
import os
from http.server import BaseHTTPRequestHandler

# Add the scripts directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from mtg_price_checker import MTGPriceChecker

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Initialize the MTG price checker
            config_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'config.json')
            price_checker = MTGPriceChecker(config_path)
            
            response_data = {
                'status': 'healthy',
                'stores_configured': len(price_checker.stores)
            }
            
            # Send response with CORS headers
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            
        except Exception as e:
            # Send error response
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            error_response = {
                'status': 'unhealthy',
                'error': str(e)
            }
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
    
    def do_OPTIONS(self):
        # Handle preflight CORS requests
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

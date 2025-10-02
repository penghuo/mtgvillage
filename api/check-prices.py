import json
import sys
import os
import traceback
from http.server import BaseHTTPRequestHandler
from typing import List, Dict, Any

# Add the scripts directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from mtg_price_checker import MTGPriceChecker

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Read request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            # Initialize the MTG price checker
            config_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'config.json')
            price_checker = MTGPriceChecker(config_path)
            
            # Get card list from request
            card_text = data.get('cards', '').strip()
            if not card_text:
                self._send_error(400, 'No cards provided')
                return
            
            # Parse card names (one per line)
            card_names = [line.strip() for line in card_text.split('\n') if line.strip()]
            if not card_names:
                self._send_error(400, 'No valid card names found')
                return
            
            # Get selected stores from request
            selected_stores = data.get('stores', [])
            if not selected_stores:
                self._send_error(400, 'No stores selected')
                return
            
            # Validate selected stores
            available_stores = set(price_checker.stores.keys())
            invalid_stores = set(selected_stores) - available_stores
            if invalid_stores:
                self._send_error(400, f'Invalid stores: {", ".join(invalid_stores)}')
                return
            
            # Process cards
            results = []
            store_stats = {store: {'available': 0, 'total_price': 0.0} for store in selected_stores}
            overall_lowest_total = 0.0
            
            for card_name in card_names:
                try:
                    if len(selected_stores) == 1:
                        # Single store mode
                        store_key = selected_stores[0]
                        result = price_checker.check_card_prices(card_name, store_key)
                        
                        # Convert to multi-store format for consistency
                        multi_result = {'card_name': card_name}
                        for store in available_stores:
                            if store == store_key:
                                multi_result[f'{store}_price'] = result.get('price', 'n/a')
                                multi_result[f'{store}_availability'] = result.get('availability', 'n/a')
                            else:
                                multi_result[f'{store}_price'] = 'n/a'
                                multi_result[f'{store}_availability'] = 'n/a'
                        
                        price = result.get('price', 'n/a')
                        if price != 'n/a':
                            multi_result['lowest_price'] = price
                            multi_result['lowest_price_store'] = store_key
                        else:
                            multi_result['lowest_price'] = 'n/a'
                            multi_result['lowest_price_store'] = 'n/a'
                        
                        results.append(multi_result)
                        
                    else:
                        # Multi-store mode - but only for selected stores
                        result = {'card_name': card_name}
                        store_prices = {}
                        
                        # Query each selected store
                        for store_key in selected_stores:
                            store_result = price_checker.check_card_prices(card_name, store_key)
                            price = store_result.get('price', 'n/a')
                            availability = store_result.get('availability', 'n/a')
                            
                            result[f'{store_key}_price'] = price
                            result[f'{store_key}_availability'] = availability
                            
                            # Track valid prices for lowest price calculation
                            if price != 'n/a' and isinstance(price, (int, float)):
                                store_prices[store_key] = price
                        
                        # Add n/a for unselected stores
                        for store_key in available_stores:
                            if store_key not in selected_stores:
                                result[f'{store_key}_price'] = 'n/a'
                                result[f'{store_key}_availability'] = 'n/a'
                        
                        # Find lowest price among selected stores
                        if store_prices:
                            lowest_store = min(store_prices.keys(), key=lambda k: store_prices[k])
                            result['lowest_price'] = store_prices[lowest_store]
                            result['lowest_price_store'] = lowest_store
                        else:
                            result['lowest_price'] = 'n/a'
                            result['lowest_price_store'] = 'n/a'
                        
                        results.append(result)
                    
                    # Update statistics for selected stores
                    for store_key in selected_stores:
                        price = results[-1].get(f'{store_key}_price', 'n/a')
                        availability = results[-1].get(f'{store_key}_availability', 'n/a')
                        
                        if price != 'n/a' and availability == 'Available':
                            store_stats[store_key]['available'] += 1
                            store_stats[store_key]['total_price'] += price
                    
                    # Update overall lowest total
                    lowest_price = results[-1].get('lowest_price', 'n/a')
                    if lowest_price != 'n/a':
                        overall_lowest_total += lowest_price
                        
                except Exception as e:
                    print(f"Error processing card '{card_name}': {e}")
                    # Add error result
                    error_result = {'card_name': card_name}
                    for store_key in available_stores:
                        error_result[f'{store_key}_price'] = 'n/a'
                        error_result[f'{store_key}_availability'] = 'n/a'
                    error_result['lowest_price'] = 'n/a'
                    error_result['lowest_price_store'] = 'n/a'
                    results.append(error_result)
            
            # Prepare summary
            summary = {
                'total_cards': len(card_names),
                'store_stats': {},
                'overall_lowest_total': overall_lowest_total
            }
            
            for store_key in selected_stores:
                store_name = price_checker.stores[store_key].name
                summary['store_stats'][store_key] = {
                    'name': store_name,
                    'available': store_stats[store_key]['available'],
                    'total_price': store_stats[store_key]['total_price']
                }
            
            # Send successful response
            response_data = {
                'success': True,
                'results': results,
                'summary': summary,
                'selected_stores': selected_stores
            }
            
            self._send_success(response_data)
            
        except json.JSONDecodeError as e:
            self._send_error(400, 'Invalid JSON in request body')
        except Exception as e:
            print(f"Error in check_prices: {e}")
            print(traceback.format_exc())
            self._send_error(500, str(e))
    
    def do_OPTIONS(self):
        # Handle preflight CORS requests
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def _send_success(self, data):
        """Send successful response with CORS headers"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        self.wfile.write(json.dumps(data).encode('utf-8'))
    
    def _send_error(self, status_code, message):
        """Send error response with CORS headers"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        error_response = {
            'success': False,
            'error': message
        }
        self.wfile.write(json.dumps(error_response).encode('utf-8'))

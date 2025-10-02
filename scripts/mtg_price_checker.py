#!/usr/bin/env python3
"""
MTG Card Price and Availability Checker

This script reads MTG card names from a text file and queries configurable
MTG store websites to get availability and pricing information.

Usage:
    python mtg_price_checker.py [--input cards.txt] [--store elegantoctopus] [--output results.csv]
"""

import json
import csv
import requests
import argparse
import sys
from typing import List, Dict, Any, Optional
from pathlib import Path


class MTGStore:
    """Base class for MTG store API interactions"""
    
    def __init__(self, store_config: Dict[str, Any]):
        self.config = store_config
        self.name = store_config.get('name', 'Unknown Store')
        self.search_url = store_config['search_url']
        self.inventory_url = store_config.get('inventory_url')  # Optional for some stores
        self.headers = store_config.get('headers', {})
        self.search_payload_template = store_config['search_payload']
        self.store_type = store_config.get('type', 'tcgplayer_pro')  # Default to original type
    
    def search_cards(self, card_name: str) -> List[Dict[str, Any]]:
        """Search for cards and return product information"""
        try:
            # Prepare search payload based on store type
            payload = self.search_payload_template.copy()
            
            if self.store_type == 'tcgplayer_pro':
                payload['query'] = card_name
            elif self.store_type == 'conductcommerce':
                payload['name'] = card_name
            
            # Make search request
            response = requests.post(
                self.search_url,
                headers=self.headers,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Handle different response formats
            if self.store_type == 'tcgplayer_pro':
                products = data.get('products', {}).get('items', [])
            elif self.store_type == 'conductcommerce':
                products = data.get('result', {}).get('listings', [])
            else:
                products = []
            
            print(f"Found {len(products)} products for '{card_name}'")
            return products
            
        except requests.exceptions.RequestException as e:
            print(f"Error searching for '{card_name}': {e}")
            return []
        except json.JSONDecodeError as e:
            print(f"Error parsing search response for '{card_name}': {e}")
            return []
    
    def get_inventory(self, product_ids: List[int]) -> List[Dict[str, Any]]:
        """Get inventory and pricing for product IDs"""
        if not product_ids:
            return []
        
        try:
            # Convert product IDs to comma-separated string
            product_ids_str = ','.join(map(str, product_ids))
            
            # Make inventory request
            inventory_url = f"{self.inventory_url}?productIds={product_ids_str}"
            response = requests.get(
                inventory_url,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            print(f"Retrieved inventory for {len(product_ids)} products")
            return data if isinstance(data, list) else []
            
        except requests.exceptions.RequestException as e:
            print(f"Error getting inventory for product IDs {product_ids}: {e}")
            return []
        except json.JSONDecodeError as e:
            print(f"Error parsing inventory response: {e}")
            return []


class MTGPriceChecker:
    """Main class for checking MTG card prices and availability"""
    
    def __init__(self, config_file: str = 'config.json'):
        self.config = self.load_config(config_file)
        self.stores = {}
        
        # Initialize stores from config
        for store_key, store_config in self.config['stores'].items():
            self.stores[store_key] = MTGStore(store_config)
    
    def load_config(self, config_file: str) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Config file '{config_file}' not found!")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error parsing config file: {e}")
            sys.exit(1)
    
    def load_card_names(self, input_file: str) -> List[str]:
        """Load card names from text file (one per line)"""
        try:
            with open(input_file, 'r') as f:
                cards = [line.strip() for line in f if line.strip()]
            print(f"Loaded {len(cards)} card names from '{input_file}'")
            return cards
        except FileNotFoundError:
            print(f"Input file '{input_file}' not found!")
            sys.exit(1)
    
    def process_tcgplayer_results(self, card_name: str, products: List[Dict], inventory_data: List[Dict]) -> Dict:
        """Process TCGPlayer Pro style search and inventory results"""
        all_skus = []
        
        # Create a mapping of product ID to product info
        product_map = {product['id']: product for product in products}
        
        # Collect all available SKUs across all products
        for item in inventory_data:
            product_id = item.get('productId')
            skus = item.get('skus', [])
            
            if product_id not in product_map:
                continue
            
            # Process each SKU (inventory item)
            for sku in skus:
                quantity = sku.get('quantity', 0)
                price = sku.get('price', 0.0)
                
                # Only include items with quantity > 0
                if quantity > 0:
                    all_skus.append({
                        'price': price,
                        'quantity': quantity
                    })
        
        # Consolidate results for this card
        if all_skus:
            # Sort by price to get lowest price
            all_skus.sort(key=lambda x: x['price'])
            lowest_price = all_skus[0]['price']
            total_quantity = sum(sku['quantity'] for sku in all_skus)
            
            return {
                'card_name': card_name,
                'availability': 'Available',
                'price': lowest_price,
                'quantity': total_quantity
            }
        else:
            # No available inventory found
            return {
                'card_name': card_name,
                'availability': 'n/a',
                'price': 'n/a',
                'quantity': 0
            }
    
    def process_conductcommerce_results(self, card_name: str, listings: List[Dict]) -> Dict:
        """Process ConductCommerce style results (Laughing Dragon MTG)"""
        all_variants = []
        
        # Collect all available variants across all listings
        for listing in listings:
            variants = listing.get('variants', [])
            
            for variant in variants:
                quantity = variant.get('quantity', 0)
                price = variant.get('price', 0.0)
                
                # Only include variants with quantity > 0
                if quantity > 0:
                    all_variants.append({
                        'price': price,
                        'quantity': quantity
                    })
        
        # Consolidate results for this card
        if all_variants:
            # Sort by price to get lowest price
            all_variants.sort(key=lambda x: x['price'])
            lowest_price = all_variants[0]['price']
            total_quantity = sum(variant['quantity'] for variant in all_variants)
            
            return {
                'card_name': card_name,
                'availability': 'Available',
                'price': lowest_price,
                'quantity': total_quantity
            }
        else:
            # No available inventory found
            return {
                'card_name': card_name,
                'availability': 'n/a',
                'price': 'n/a',
                'quantity': 0
            }
    
    def check_card_prices(self, card_name: str, store_key: str) -> Dict:
        """Check prices for a single card at a specific store - return one consolidated result"""
        if store_key not in self.stores:
            print(f"Store '{store_key}' not configured!")
            return {
                'card_name': card_name,
                'availability': 'n/a',
                'price': 'n/a',
                'quantity': 0
            }
        
        store = self.stores[store_key]
        print(f"\nChecking prices for '{card_name}' at {store.name}...")
        
        # Step 1: Search for products
        products = store.search_cards(card_name)
        if not products:
            print(f"No products found for '{card_name}'")
            return {
                'card_name': card_name,
                'availability': 'n/a',
                'price': 'n/a',
                'quantity': 0
            }
        
        # Handle different store types
        if store.store_type == 'conductcommerce':
            # For ConductCommerce (Laughing Dragon), all data is in the search response
            result = self.process_conductcommerce_results(card_name, products)
            return result
        else:
            # For TCGPlayer Pro, need separate inventory call
            # Step 2: Get inventory for product IDs
            product_ids = [product['id'] for product in products]
            inventory_data = store.get_inventory(product_ids)
            
            if not inventory_data:
                print(f"No inventory data found for '{card_name}'")
                return {
                    'card_name': card_name,
                    'availability': 'n/a',
                    'price': 'n/a',
                    'quantity': 0
                }
            
            # Step 3: Process results
            result = self.process_tcgplayer_results(card_name, products, inventory_data)
            return result
    
    def check_card_across_stores(self, card_name: str) -> Dict:
        """Check prices for a single card across all configured stores"""
        print(f"\nChecking prices for '{card_name}' across all stores...")
        
        # Initialize result with card name
        result = {'card_name': card_name}
        store_prices = {}
        
        # Query each store
        for store_key in self.stores.keys():
            try:
                store_result = self.check_card_prices(card_name, store_key)
                price = store_result.get('price', 'n/a')
                availability = store_result.get('availability', 'n/a')
                
                # Add store-specific columns
                result[f'{store_key}_price'] = price
                result[f'{store_key}_availability'] = availability
                
                # Track valid prices for lowest price calculation
                if price != 'n/a' and isinstance(price, (int, float)):
                    store_prices[store_key] = price
                    
            except Exception as e:
                print(f"Error querying {store_key} for '{card_name}': {e}")
                result[f'{store_key}_price'] = 'n/a'
                result[f'{store_key}_availability'] = 'n/a'
        
        # Find lowest price and corresponding store
        if store_prices:
            lowest_store = min(store_prices.keys(), key=lambda k: store_prices[k])
            result['lowest_price'] = store_prices[lowest_store]
            result['lowest_price_store'] = lowest_store
        else:
            result['lowest_price'] = 'n/a'
            result['lowest_price_store'] = 'n/a'
        
        return result

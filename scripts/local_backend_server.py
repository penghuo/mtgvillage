#!/usr/bin/env python3
"""Local development API server for MTG Price Checker."""

from __future__ import annotations

import json
import signal
import sys
from argparse import ArgumentParser
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Dict, Any, List
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"

sys.path.insert(0, str(SCRIPTS_DIR))

from mtg_price_checker import MTGPriceChecker  # noqa: E402


def build_price_checker() -> MTGPriceChecker:
    config_path = SCRIPTS_DIR / "config.json"
    return MTGPriceChecker(config_file=str(config_path))


class LocalApiHandler(BaseHTTPRequestHandler):
    server_version = "MTGVillageLocalAPI/1.0"

    @property
    def price_checker(self) -> MTGPriceChecker:
        if getattr(self.server, "price_checker", None) is None:
            self.server.price_checker = build_price_checker()
        return self.server.price_checker

    # Utility helpers -------------------------------------------------
    def _set_cors_headers(self, status: int) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _send_json(self, status: int, payload: Dict[str, Any]) -> None:
        self._set_cors_headers(status)
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode("utf-8"))

    def _parse_json_body(self) -> Dict[str, Any]:
        length_header = self.headers.get("Content-Length")
        if not length_header:
            return {}
        length = int(length_header)
        data = self.rfile.read(length)
        if not data:
            return {}
        return json.loads(data.decode("utf-8"))

    # HTTP verb handlers ----------------------------------------------
    def do_OPTIONS(self) -> None:  # noqa: N802
        self._set_cors_headers(200)
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/api/stores":
            self._handle_get_stores()
        elif path == "/api/health":
            self._handle_health()
        else:
            self._send_json(404, {"success": False, "error": "Not Found"})

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/api/check-prices":
            self._handle_check_prices()
        else:
            self._send_json(404, {"success": False, "error": "Not Found"})

    # Endpoint implementations ---------------------------------------
    def _handle_get_stores(self) -> None:
        try:
            stores_payload = []
            for store_key, store in self.price_checker.stores.items():
                stores_payload.append(
                    {
                        "key": store_key,
                        "name": store.name,
                        "type": store.store_type,
                    }
                )
            self._send_json(200, {"success": True, "stores": stores_payload})
        except Exception as exc:  # pragma: no cover - dev helper
            self._send_json(500, {"success": False, "error": str(exc)})

    def _handle_health(self) -> None:
        try:
            self._send_json(
                200,
                {
                    "status": "healthy",
                    "stores_configured": len(self.price_checker.stores),
                },
            )
        except Exception as exc:  # pragma: no cover
            self._send_json(500, {"status": "unhealthy", "error": str(exc)})

    def _handle_check_prices(self) -> None:
        try:
            payload = self._parse_json_body()
        except json.JSONDecodeError:
            self._send_json(400, {"success": False, "error": "Invalid JSON"})
            return

        try:
            card_text = (payload.get("cards") or "").strip()
            if not card_text:
                self._send_json(400, {"success": False, "error": "No cards provided"})
                return

            card_names = [line.strip() for line in card_text.split("\n") if line.strip()]
            if not card_names:
                self._send_json(400, {"success": False, "error": "No valid card names found"})
                return

            selected_stores: List[str] = payload.get("stores", []) or []
            if not selected_stores:
                self._send_json(400, {"success": False, "error": "No stores selected"})
                return

            available_stores = set(self.price_checker.stores.keys())
            invalid_stores = set(selected_stores) - available_stores
            if invalid_stores:
                self._send_json(
                    400,
                    {
                        "success": False,
                        "error": f"Invalid stores: {', '.join(sorted(invalid_stores))}",
                    },
                )
                return

            results: List[Dict[str, Any]] = []
            store_stats = {store: {"available": 0, "total_price": 0.0} for store in selected_stores}
            overall_lowest_total = 0.0

            for card_name in card_names:
                try:
                    result = self._process_card(card_name, selected_stores, available_stores)
                    results.append(result)

                    for store_key in selected_stores:
                        price = result.get(f"{store_key}_price", "n/a")
                        availability = result.get(f"{store_key}_availability", "n/a")
                        if price != "n/a" and availability == "Available":
                            store_stats[store_key]["available"] += 1
                            store_stats[store_key]["total_price"] += price  # type: ignore[operator]

                    lowest_price = result.get("lowest_price", "n/a")
                    if isinstance(lowest_price, (int, float)):
                        overall_lowest_total += lowest_price
                except Exception as exc:  # pragma: no cover
                    error_result = {"card_name": card_name}
                    for store_key in available_stores:
                        error_result[f"{store_key}_price"] = "n/a"
                        error_result[f"{store_key}_availability"] = "n/a"
                    error_result["lowest_price"] = "n/a"
                    error_result["lowest_price_store"] = "n/a"
                    error_result["error"] = str(exc)
                    results.append(error_result)

            summary = {
                "total_cards": len(card_names),
                "store_stats": {},
                "overall_lowest_total": overall_lowest_total,
            }
            for store_key in selected_stores:
                store_name = self.price_checker.stores[store_key].name
                summary["store_stats"][store_key] = {
                    "name": store_name,
                    "available": store_stats[store_key]["available"],
                    "total_price": store_stats[store_key]["total_price"],
                }

            self._send_json(
                200,
                {
                    "success": True,
                    "results": results,
                    "summary": summary,
                    "selected_stores": selected_stores,
                },
            )
        except Exception as exc:  # pragma: no cover
            self._send_json(500, {"success": False, "error": str(exc)})

    # Helper methods --------------------------------------------------
    def _process_card(
        self,
        card_name: str,
        selected_stores: List[str],
        available_stores: set[str],
    ) -> Dict[str, Any]:
        price_checker = self.price_checker
        result: Dict[str, Any] = {"card_name": card_name}
        store_prices: Dict[str, float] = {}

        if len(selected_stores) == 1:
            store_key = selected_stores[0]
            store_result = price_checker.check_card_prices(card_name, store_key)
            for store in available_stores:
                key_price = f"{store}_price"
                key_availability = f"{store}_availability"
                if store == store_key:
                    result[key_price] = store_result.get("price", "n/a")
                    result[key_availability] = store_result.get("availability", "n/a")
                else:
                    result[key_price] = "n/a"
                    result[key_availability] = "n/a"
            price = result.get(f"{store_key}_price", "n/a")
            if isinstance(price, (int, float)):
                result["lowest_price"] = price
                result["lowest_price_store"] = store_key
            else:
                result["lowest_price"] = "n/a"
                result["lowest_price_store"] = "n/a"
            return result

        for store_key in selected_stores:
            store_result = price_checker.check_card_prices(card_name, store_key)
            price = store_result.get("price", "n/a")
            availability = store_result.get("availability", "n/a")
            result[f"{store_key}_price"] = price
            result[f"{store_key}_availability"] = availability
            if isinstance(price, (int, float)):
                store_prices[store_key] = price

        for store_key in available_stores:
            if store_key not in selected_stores:
                result[f"{store_key}_price"] = "n/a"
                result[f"{store_key}_availability"] = "n/a"

        if store_prices:
            lowest_store = min(store_prices, key=store_prices.get)
            result["lowest_price"] = store_prices[lowest_store]
            result["lowest_price_store"] = lowest_store
        else:
            result["lowest_price"] = "n/a"
            result["lowest_price_store"] = "n/a"

        return result


def parse_args():
    parser = ArgumentParser(description="Run local MTG Price Checker API server")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface to bind")
    parser.add_argument("--port", type=int, default=3000, help="Port for the API server")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    server = ThreadingHTTPServer((args.host, args.port), LocalApiHandler)
    print(f"Local API server running at http://{args.host}:{args.port}")

    def shutdown(signum, frame):  # noqa: ANN001, D401
        server.shutdown()

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

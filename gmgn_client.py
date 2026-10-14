#!/usr/bin/env python3
"""gmgn-client — client Python untuk internal API gmgn.ai.

Terinsinasi dari reverse-engineering bundle JS production GMGN.
Auth: fingerprint TLS Chrome (curl_cffi) + header Referer. Tanpa API key.

Pemakaian:
    pip install curl_cffi
    from gmgn_client import Gmgn
    g = Gmgn()
    print(g.rank_wallets("sol", "1h", tag="smart_degen", limit=10))
"""
import time
import random
from typing import Optional
from curl_cffi import requests

BASE = "https://gmgn.ai"
IMPERSONATES = ["chrome131", "chrome124", "chrome120", "safari17_0"]


class GmgnError(Exception):
    def __init__(self, code, message, data=None):
        super().__init__(f"GMGN error {code}: {message}")
        self.code = code
        self.message = message
        self.data = data


class Gmgn:
    def __init__(self, login_cookies: Optional[dict] = None, min_delay=0.2):
        self.min_delay = min_delay
        self._last = 0.0
        self._imp_idx = 0
        self.session = requests.Session(impersonate=IMPERSONATES[0])
        self.headers = {
            "Accept": "application/json",
            "Referer": BASE + "/",
            "Origin": BASE,
        }
        if login_cookies:
            for k, v in login_cookies.items():
                self.session.cookies.set(k, v, domain=".gmgn.ai")
        self.warmup()

    # --- plumbing ---------------------------------------------------------
    def _throttle(self):
        wait = self.min_delay - (time.monotonic() - self._last)
        if wait > 0:
            time.sleep(wait + random.uniform(0, 0.15))
        self._last = time.monotonic()

    def _rotate(self):
        self._imp_idx = (self._imp_idx + 1) % len(IMPERSONATES)
        self.session = requests.Session(impersonate=IMPERSONATES[self._imp_idx])

    def _request(self, method, path, *, params=None, json_body=None, retries=3):
        for attempt in range(retries):
            self._throttle()
            try:
                r = self.session.request(
                    method, BASE + path,
                    params=params, json=json_body, headers=self.headers, timeout=25,
                )
                if r.status_code == 403:  # Cloudflare challenge: rotate & backoff
                    self._rotate()
                    time.sleep(2 ** attempt + random.uniform(0, 2))
                    continue
                if r.status_code == 404:
                    raise GmgnError(404, f"endpoint not found: {path}")
                body = r.json()
            except GmgnError:
                raise
            except Exception as e:
                if attempt == retries - 1:
                    raise
                time.sleep(2 ** attempt)
                continue
            if body.get("code") != 0:
                raise GmgnError(body.get("code"), body.get("message") or body.get("msg"), body.get("data"))
            return body.get("data")
        raise GmgnError(-1, "exhausted retries (Cloudflare)")

    def get(self, path, **params):
        return self._request("GET", path, params=params or None)

    def post(self, path, json_body=None, **params):
        return self._request("POST", path, params=params or None, json_body=json_body)

    def warmup(self):
        """Segarkan __cf_bm dengan hit ringan ke endpoint ranking."""
        try:
            self._request("GET", "/defi/quotation/v1/rank/sol/wallets/7d", retries=2)
        except Exception:
            pass

    # --- ranking / smart money -------------------------------------------
    def rank_wallets(self, chain="sol", period="1h", *, tag=None, limit=50, **extra):
        """period: 1h|6h|24h|7d|30d. tag: smart_degen|renowned|snipe_bot|fresh_wallet|kol"""
        p = {"limit": limit, **extra}
        if tag:
            p["tag"] = tag
        return self.get(f"/api/v1/rank/{chain}/wallets/{period}", **p)

    def rank_swaps(self, chain="sol", period="1h", **extra):
        return self.get(f"/api/v1/rank/{chain}/swaps/{period}", **extra)

    def bluechip_rank(self, chain="eth", filters=None, **extra):
        params = dict(extra)
        if filters:
            params["filters"] = filters  # array -> repeat
        return self._request("GET", f"/api/v1/bluechip_rank/{chain}", params=params)

    # --- token ------------------------------------------------------------
    def token_info(self, chain, mint):
        return self.get(f"/api/v1/token_info/{chain}/{mint}")

    def token_stat(self, chain, mint):
        return self.get(f"/api/v1/token_stat/{chain}/{mint}")

    def token_security(self, chain, mint):
        if chain == "sol":
            path = f"/api/v1/token_security_sol/sol/{mint}"
        elif chain == "tron":
            path = f"/defi/quotation/v1/tokens/security?chain=tron&addresses={mint}"
        else:
            path = f"/api/v1/token_security_evm/{chain}/{mint}"
        return self._request("GET", path)

    def token_dev_info(self, chain, mint):
        return self.get(f"/api/v1/token_dev_info/{chain}/{mint}")

    def token_fee_info(self, chain, mint):
        return self.get(f"/api/v1/token_fee_info/{chain}/{mint}")

    def top_buyers(self, chain, mint):
        return self.get(f"/api/v1/tokens/top_buyers/{chain}/{mint}")

    # --- trades & holder stat (VAS) ---------------------------------------
    def token_trades(self, chain, mint, limit=50, **extra):
        return self.get(f"/vas/api/v1/token_trades/{chain}/{mint}", limit=limit, **extra)

    def token_holder_stat(self, chain, mint, **extra):
        return self.get(f"/vas/api/v1/token_holder_stat/{chain}/{mint}", **extra)

    def token_trader_stat(self, chain, mint, **extra):
        return self.get(f"/vas/api/v1/token_trader_stat/{chain}/{mint}", **extra)

    # --- candles & price ----------------------------------------------------
    def token_candles(self, chain, mint, resolution="1m", from_ts=0, to_ts=9999999999):
        return self.get(f"/api/v1/token_candles/{chain}/{mint}",
                        resolution=resolution, **{"from": from_ts, "to": to_ts})

    def realtime_price(self, chain, mint, decimals=6):
        return self.get(f"/defi/quotation/v1/{chain}/tokens/realtime_token_price",
                        address=mint, decimals=decimals)

    # --- wallet / PnL ---------------------------------------------------------
    def wallet_common_stat(self, chain, address):
        return self.get(f"/api/v1/wallet_common_stat/{chain}/{address}")

    def wallet_stat(self, chain, address, period="7d", **extra):
        return self.get(f"/api/v1/wallet_stat/{chain}/{address}/{period}", **extra)

    def wallet_profit_stat(self, chain, address, period="7d"):
        # pf prefix; sebagian data butuh login (authType Access)
        return self.get(f"/pf/api/v1/wallet/{chain}/{address}/profit_stat/{period}")

    def wallet_holding(self, chain, address):
        return self.get(f"/api/v1/wallet/{chain}/{address}/holding")

    # --- discovery -------------------------------------------------------------
    def new_pairs(self, chain="sol", period="1h", **extra):
        return self.get(f"/api/v1/pairs/{chain}/new_pairs/{period}", **extra)

    def pump_rank(self, chain="sol", window="1h"):
        return self.get(f"/defi/quotation/v1/rank/{chain}/pump/{window}")

    def gas_prices(self):
        return self.get("/api/v1/gas_price_list")


if __name__ == "__main__":
    import json
    g = Gmgn()
    print("== top smart-money wallets (sol/1h) ==")
    for w in (g.rank_wallets("sol", "1h", tag="smart_degen", limit=5)["rank"] or []):
        print(" ", w.get("address"), "profit:", w.get("realized_profit"))
    pairs = g.new_pairs("sol", "1h")["pairs"]
    if pairs:
        mint = pairs[0]["base_address"]
        print("== new pair sample:", mint, "==")
        print("  price:", g.realtime_price("sol", mint, 6))
        print("  stat:", json.dumps(g.token_stat("sol", mint))[:200])

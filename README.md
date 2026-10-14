# GMGN API Reverse Engineering

Reverse-engineered map of gmgn.ai's internal (undocumented) web API, extracted from
their production JavaScript bundles and verified live with real requests.

**Auth model:** no API key or bearer token is needed for public data. Access is
gated by TLS fingerprint (Chrome impersonation via [curl_cffi](https://github.com/lexiforest/curl_cffi))
plus a `Referer: https://gmgn.ai/` header. Login cookies (`sid`, `_wt`, `_csrf`)
are only required for account features (watchlists, follows, VIP).

## Contents

| File | Description |
|---|---|
| [`gmgn_client.py`](gmgn_client.py) | Ready-to-use Python client with rate limiting and Cloudflare retry/rotation |
| [`api-map/gmgn-api-map.md`](api-map/gmgn-api-map.md) | Full endpoint map with parameters and usage rules |
| [`api-map/gmgn-endpoints.txt`](api-map/gmgn-endpoints.txt) | 167 raw endpoint templates extracted from the bundles |
| [`api-map/gmgn-endpoints-context.json`](api-map/gmgn-endpoints-context.json) | Source-code context for each endpoint (to see exact param objects) |

## Quick start

```bash
pip install curl_cffi
python gmgn_client.py
```

```python
from gmgn_client import Gmgn

g = Gmgn()
rank = g.rank_wallets("sol", "1h", tag="smart_degen", limit=10)
price = g.realtime_price("sol", "<mint>", decimals=6)
```

## API surface (highlights)

- **Prefixes:** `/api/v1/` (core), `/vas/api/v1/` (trades/holder stat), `/pf/api/v1/`
  (wallet PnL), `/trs/api/v1/` (trenches), `/defi/quotation/v1/` (ranks & realtime price)
- **Ranking:** wallet ranks, smart money, bluechip ranks, new pairs, pump/moonshot feeds
- **Token:** info, stats, security (SOL/EVM/Tron variants), dev info, fees, top buyers
- **Market data:** trades, candles (OHLC + mcap), realtime price polling
- **Wallet:** stats, PnL, holdings
- **Realtime:** `wss://ws.gmgn.ai` and `wss://sub-tx-hash.gmgn.ai` (subscribe protocol not reversed; REST polling is sufficient for most uses)

## Legal / disclaimer

This is research on a public web app's own frontend API for interoperability and
educational purposes. Respect their service and rate limits; the API is unofficial
and can change or break at any time. No credentials or private data are included.

## License

MIT

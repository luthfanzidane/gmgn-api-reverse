# GMGN.ai internal API — reverse-engineered map
Diperoleh dari bundle JS production gmgn.ai (22 file, 14 MB), diverifikasi live 2026-10-14.

## Cara pemakaian

```python
from curl_cffi import requests

s = requests.Session(impersonate="chrome131")  # WAJIB: TLS fingerprint Chrome
h = {
  "Accept": "application/json",
  "Referer": "https://gmgn.ai/",     # WAJIB di sebagian besar endpoint
  "Origin": "https://gmgn.ai",
}
r = s.get("https://gmgn.ai/api/v1/rank/sol/wallets/1h?tag=smart_degen&limit=20", headers=h)
print(r.json())
```

- **Tidak butuh Bearer/api key untuk data publik.** Auth = fingerprint TLS Chrome (`impersonate="chrome131"`) + header Referer. curl biasa = 403 Cloudflare.
- Cookie: `__cf_bm` diurus otomatis oleh Session. Cookie login (`sid`,`_wt`,`_csrf`) hanya untuk fitur akun (follow, watchlist, VIP) — endpoint bertanda `authType: Access` di bundle.
- Response envelope: `{"code":0,"message":"success","data":...}`; `code != 0` = error.
- Rate-limit tak resmi: jaga 2–5 req paralel, jeda 200–500 ms.
- Prefix rute: `/api/v1/` (core), `/vas/api/v1/` (trades & holder stat), `/pf/api/v1/` (portfolio/wallet PnL), `/trs/api/v1/` (trenches), `/defi/quotation/v1/` (ranking & harga), `/mrwapi/v1/` (bags royalty). Semua di host `https://gmgn.ai`.

## Chain slug
`sol`, `eth`, `bsc`, `base`, `arb`, `polygon`, `sui`, `tron`, `blast`, `linea`, `avalanche` (lihat `bluechip_rank`/`new_pairs` param chain).

## Endpoint terverifikasi live (2026-10-14)

### Ranking wallet / smart money
- `GET /api/v1/rank/{chain}/wallets/{period}?tag={tag}&limit={n}`
  - period: `1h 6h 24h 7d 30d`; tag: `smart_degen, renowned, snipe_bot, fresh_wallet, kol` dsb.
  - → `data.rank[]` (address, realized_profit, arc_balance, tags, winrate...)
- `GET /api/v1/rank/{chain}/swaps/{period}` — ranking berdasar volume swap
- `GET /api/v1/rank/{chain}/wallet_followed` — wallet yang paling banyak di-follow
- `GET /api/v1/bluechip_rank/{chain}?filters[]=...` — ranking holder bluechip
- `GET /defi/quotation/v1/rank/{chain}/wallets/{period}` — varian quotation (sudah teruji 200)

### Token
- `GET /api/v1/token_info/{chain}/{mint}` → profil lengkap (symbol, price, liquidity, pool)
- `GET /api/v1/token_stat/{chain}/{mint}` → holder_count, signal_count, degen_call_count, top_rat_trader_pct...
- `GET /api/v1/token_security_sol/sol/{mint}` (SOL; EVM pakai `/api/v1/token_security_evm/{chain}/{addr}`, Tron pakai `/defi/quotation/v1/tokens/security`) → top_10_holder_rate, mint/renounce/freeze flags
- `GET /api/v1/token_dev_info/{chain}/{mint}` → creator_address, creator balance, fund_from
- `GET /api/v1/tokens/top_buyers/{chain}/{mint}` → data holders/top buyers
- `GET /api/v1/token_fee_info/{chain}/{mint}` → fee & holder rewards
- `POST /api/v1/token_info_brief` body `{"chain":"sol","addresses":[mint]}` (kadang CF-challenge; GET `token_info` lebih stabil)
- `POST /api/v1/mutil_window_token_info` body multi-window

### Trades & candles
- `GET /vas/api/v1/token_trades/{chain}/{mint}?limit=10` → `data.history[]` (maker, base/quote amount, timestamp) ⚠️ prefix `/vas`
- `GET /vas/api/v1/token_holder_stat/{chain}/{mint}` → smart_degen_count, insider_count, dex_bot_count...
- `GET /api/v1/token_candles/{chain}/{mint}?resolution=1m&from={unix}&to={unix}` → `data.list[]`; juga `token_mcap_candles`
- `GET /defi/quotation/v1/{chain}/tokens/realtime_token_price?address={mint}&decimals={d}` → `data.usd_price` (poll)
- `GET /api/v1/dex_trades_polling` — feed trade (long-poll)
- `GET /api/v1/agged_token_trades/{chain}/{mint}` — trades teragregasi

### Wallet / PnL
- `GET /api/v1/wallet_common_stat/{chain}/{addr}` → tags, rank, avatar (teruji)
- `GET /api/v1/wallet_stat/{chain}/{addr}/{period}` (period: `7d` dll)
- `GET /pf/api/v1/wallet/{chain}/{addr}/profit_stat/{period}` → PnL breakdown (authType Access — mungkin butuh login)
- `GET /api/v1/wallet/{chain}/{addr}/holding` & `/holdings` → posisi
- `GET /api/v1/wallets/daily_profits`, `wallets/holdings`, `wallets/balances` (POST batch)
- `GET /pf/api/v1/wallet/{chain}/{addr}/wallet_token_info?token_address={mint}`
- `GET /api/v1/wallet_token_info/{chain}/{addr}/{mint}`

### Pasar / discovery
- `GET /api/v1/pairs/{chain}/new_pairs/{period}` → `data.pairs[]` (address, base_address, liquidity, renounced...) (teruji)
- `GET /defi/quotation/v1/rank/{chain}/pump/{window}` & `pump_ranks/{window}` — feed Pump.fun (teruji)
- `GET /defi/quotation/v1/rank/{chain}/moonshot|flap|ray_launchpad/{window}` — launchpad lain
- `GET /api/v1/live/token_list/{chain}`, `token_preview/{chain}/{mint}`
- `GET /api/v1/trenches_rank` (di bundle: `POST /trs/api/v1/trenches_rank` — perlu body; belum terbongkar bentuknya)
- `GET /api/v1/gas_price_list` → gas semua chain (teruji)
- `GET /api/v1/token_prices` (GET, params map)
- `GET /api/v1/search_v3|v4` — pencarian token/wallet

### Sinyal / AI / TG / Twitter
- `GET /vas/api/v1/token-signal/bytoken|rank`, `POST /vas/api/v1/token-signal/v2`
- `GET /api/v1/token-kline-event`
- `GET /api/v1/tg_calls/klines/{chain}/{mint}`, `discord_calls/klines/{chain}/{mint}`
- `GET /api/v1/twitter/token/search`, `user_profile`, `messages`
- `GET /api/v1/token_ai_narrative/{chain}/{mint}`

### Akun (butuh cookie login: sid/_wt/_csrf)
follow/follow_wallet, follow_token/group/*, remark_wallets, user_profile, cashback/*, vip, activity/*, rebate/*, push_switch, x/auth/* — semua di `/api/v1/` atau `/defi/quotation/v1/`. Lihat `gmgn-endpoints.txt` untuk daftar literal lengkapnya.

## Realtime
- `wss://ws.gmgn.ai` — WS utama (kline/trade push; protokol subscribe belum di-RE, butuh inspeksi frame via browser)
- `wss://sub-tx-hash.gmgn.ai/` — push status transaksi
- GMGN juga konek `wss://beta.helius-rpc.com?api-key=...` (RPC Solana pihak ketiga)
- Praktisnya: REST polling `realtime_token_price` / `dex_trades_polling` sudah cukup untuk embed.

## File artefak
- `~/gmgn-endpoints.txt` — 167 template endpoint
- `~/gmgn-endpoints-context.json` — snippet kode asal tiap endpoint (untuk lihat param object)
- `/tmp/rev/gmgn-bundles/` — 22 bundle JS mentah (14 MB)
- `/tmp/rev/venv` — venv dengan curl_cffi 0.13.0

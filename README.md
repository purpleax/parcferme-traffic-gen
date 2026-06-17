# parcferme-traffic-gen

Session-based HTTP traffic simulator for WAF baseline generation, tuned for [parcferme.fastlylab.com](https://parcferme.fastlylab.com) — an authenticated F1 memorabilia demo site.

> **Authorised use only.** This tool is intended for use against lab environments you own or have explicit permission to test.

## How it works

Rather than crawling links, the script models **user journeys** — predefined sequences of pages that represent realistic navigation patterns. Each thread independently and continuously runs journeys, picking the next one at random based on configured weights.

### Journey model

| Journey | Path sequence | Weight |
|---|---|---|
| `browse` | `/` | 10% |
| `shop` | `/ → /shop` | 12% |
| `shop-p2` | `/ → /shop?page=2` | 8% |
| `new-arrivals` | `/ → /shop?sort=newest` | 10% |
| `product-view` | `/ → /shop → /product/<random>` | 25% |
| `login` | `/ → /login` | 12% |
| `register` | `/ → /login → /register` | 8% |
| `cart` | `/ → /shop → /product/<random> → /cart` | 8% |
| `account` | `/ → /login → /account/orders` | 2% |
| `api-docs` | `/api/docs` | 5% |

Product pages are picked randomly from all 24 items in the catalogue each time a product journey runs, spreading traffic evenly across the full catalogue.

### Realism features

- **`requests.Session()` per journey** — cookies persist across steps within a session, matching real browser behaviour. Each journey starts a fresh session.
- **Referer headers** — each step sets `Referer` to the previous page URL, producing believable navigation chains.
- **User-agent rotation** — a random UA (Chrome, Firefox, Safari, Edge) is picked per journey and held constant throughout it.
- **Gaussian timing** — delays between page requests use `random.gauss(delay, delay * 0.4)` floored at 0.5 s, so traffic is never perfectly uniform. A longer inter-journey pause (`delay * 4`) simulates idle/think time between visits.
- **Proxy rotation** — one proxy is picked randomly per journey from `proxies.txt`.

## Requirements

- Python 3.8+
- `requests`

```bash
pip install -r requirements.txt
```

## Usage

### Run directly

```bash
python3 traffic_gen.py --target https://parcferme.fastlylab.com
```

```
Options:
  --target   Base URL to simulate traffic against (required)
  --delay    Mean seconds between page requests within a journey (default: 2.0)
  --threads  Number of concurrent simulated users (default: 1)
```

Examples:

```bash
# Single user, default timing
python3 traffic_gen.py --target https://parcferme.fastlylab.com

# 8 concurrent users, faster pacing
python3 traffic_gen.py --target https://parcferme.fastlylab.com --delay 1.5 --threads 8
```

Stop with `Ctrl-C`.

### Run with Docker

```bash
# Build (bakes proxies.txt into the image)
docker build -t parcferme-traffic-gen .

# Run with defaults (parcferme.fastlylab.com, 4 threads, ~2s delay)
docker run --rm parcferme-traffic-gen

# Override settings
docker run --rm parcferme-traffic-gen --target https://parcferme.fastlylab.com --delay 1 --threads 10
```

> If you update `proxies.txt`, rebuild the image for the changes to take effect.

## Proxy configuration

Create `proxies.txt` in the same directory as the script. One proxy per line:

```
ip:port:username:password
```

Example:

```
192.168.1.100:8080:myuser:mypassword
10.0.0.1:3128:proxyuser:proxypass
```

One proxy is selected randomly per journey session. If the file is missing or empty, the script runs without proxies.

## Extending

**Add a journey:** append a `(name, [path, ...], weight)` tuple to `JOURNEYS` and rebalance weights to sum to `1.0`.

**Add a product:** append the slug to `PRODUCTS`.

**Use product randomisation in a new journey:** include the string `"PRODUCT"` as a path step — it resolves to a random product slug at runtime:

```python
JOURNEYS = [
    ...
    ("wishlist", ["/", "/shop", "PRODUCT", "/wishlist"], 0.05),
]
```

## Files

| File | Purpose |
|---|---|
| `traffic_gen.py` | Main script |
| `proxies.txt` | Proxy list (ip:port:user:pass, one per line) |
| `requirements.txt` | Python dependencies |
| `Dockerfile` | Container definition |

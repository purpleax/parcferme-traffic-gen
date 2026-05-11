# traffic_gen

A multi-threaded, session-based HTTP traffic simulator for generating realistic baseline traffic against a known web application. Designed for WAF testing and traffic baselining in authorised lab environments.

## How it works

Rather than crawling links, the script models **user journeys** — predefined sequences of pages that represent realistic navigation patterns. Each thread independently and continuously runs journeys, picking the next one at random based on configured weights.

### Journey model

| Journey | Path sequence | Weight |
|---|---|---|
| browse | `/` | 30% |
| login | `/` → `/login` | 25% |
| register | `/` → `/user_register` | 20% |
| contact | `/` → `/contact` | 15% |
| forgot-password | `/` → `/login` → `/forgot_password` | 10% |

Weights reflect realistic user behaviour: the homepage receives the most traffic, and deep flows like password recovery are proportionally rare.

### Realism features

- **`requests.Session()` per journey** — cookies persist across steps within a session, matching real browser behaviour. Each journey starts a fresh session.
- **Referer headers** — each step sets `Referer` to the previous page URL, producing believable navigation chains.
- **User-agent rotation** — a random UA (Chrome, Firefox, Safari, Edge) is picked per journey and held constant throughout it.
- **Gaussian timing** — delays between page requests use `random.gauss(delay, delay * 0.4)` floored at 0.5 s, so traffic is never perfectly uniform. A longer inter-journey pause (`delay * 4`) simulates idle/think time between visits.
- **Proxy rotation** — one proxy is picked randomly per journey from `proxies.txt`.

## Requirements

- Python 3.7+
- `requests`

```bash
pip install -r requirements.txt
```

## Usage

### Run directly

```bash
python3 traffic_gen.py --target https://example.com
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
python3 traffic_gen.py --target https://www.fastlylab.com

# 8 concurrent users, faster pacing
python3 traffic_gen.py --target https://www.fastlylab.com --delay 1.5 --threads 8
```

Stop with `Ctrl-C`.

### Run with Docker

```bash
# Build (bakes proxies.txt into the image)
docker build -t traffic-gen .

# Run with defaults (fastlylab.com, 4 threads, ~2s delay)
docker run --rm traffic-gen

# Override settings
docker run --rm traffic-gen --target https://example.com --delay 1 --threads 10
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

## Adding pages

Edit the `JOURNEYS` list at the top of `traffic_gen.py`:

```python
JOURNEYS = [
    ("browse",          ["/"],                               0.30),
    ("login",           ["/", "/login"],                     0.25),
    ("register",        ["/", "/user_register"],             0.20),
    ("contact",         ["/", "/contact"],                   0.15),
    ("forgot-password", ["/", "/login", "/forgot_password"], 0.10),
    # Add new journeys here:
    ("product",         ["/", "/products", "/products/demo"], 0.00),
]
```

Adjust the weights so they sum to `1.0`.

## Files

| File | Purpose |
|---|---|
| `traffic_gen.py` | Main script |
| `proxies.txt` | Proxy list (ip:port:user:pass, one per line) |
| `requirements.txt` | Python dependencies |
| `Dockerfile` | Container definition |

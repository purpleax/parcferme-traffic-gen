#!/usr/bin/env python3
import argparse
import sys
import time
import threading
import random
import os

import requests

# ——— Configuration ———

UA_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/14.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:102.0) Gecko/20100101 Firefox/102.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:112.0) Gecko/20100101 Firefox/112.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/115.0.5790.102 Safari/537.36 Edg/115.0.1901.183",
]

HEADERS_BASE = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# All 24 product pages. "PRODUCT" in a journey path is replaced with a random pick at runtime.
PRODUCTS = [
    "/product/monaco-hairpin-fine-art-print",
    "/product/1992-monza-podium-replica-helmet",
    "/product/paddock-pass-collection-1984-1999",
    "/product/1-8-scale-championship-car-2021-season",
    "/product/carbon-front-wing-endplate-2019-spec",
    "/product/race-worn-nomex-gloves-silverstone-1997",
    "/product/team-cap-2026-limited-edition",
    "/product/1-18-classic-v12-spa-winner-1995",
    "/product/1976-season-poster-restored-archive",
    "/product/1988-season-tribute-mini-helmet-1-2",
    "/product/race-suit-replica-scuderia-veloce-2024",
    "/product/visor-tear-off-set-monaco",
    "/product/night-race-photography-marina-bay",
    "/product/spa-eau-rouge-panorama-lithograph",
    "/product/f1-steering-wheel-replica-fully-wired",
    "/product/1-43-grid-set-full-2026-season",
    "/product/carbon-brake-disc-caliper-display",
    "/product/carbon-track-spec-helmet-shell",
    "/product/magnesium-wheel-rim-race-used",
    "/product/pit-crew-fireproof-suit-northline-racing",
    "/product/pit-board-final-lap-display",
    "/product/driver-boots-practice-session-worn",
    "/product/podium-champagne-signed-magnum",
    "/product/wind-tunnel-model-front-wing-section",
]

# (name, path_sequence, weight)
# "PRODUCT" is resolved to a random product slug per journey run.
JOURNEYS = [
    ("browse",       ["/"],                                    0.10),
    ("shop",         ["/", "/shop"],                           0.12),
    ("shop-p2",      ["/", "/shop?page=2"],                    0.08),
    ("new-arrivals", ["/", "/shop?sort=newest"],               0.10),
    ("product-view", ["/", "/shop", "PRODUCT"],                0.25),
    ("login",        ["/", "/login"],                          0.12),
    ("register",     ["/", "/login", "/register"],             0.08),
    ("cart",         ["/", "/shop", "PRODUCT", "/cart"],       0.08),
    ("account",      ["/", "/login", "/account/orders"],       0.02),
    ("api-docs",     ["/api/docs"],                            0.05),
]

_NAMES   = [j[0] for j in JOURNEYS]
_PATHS   = [j[1] for j in JOURNEYS]
_WEIGHTS = [j[2] for j in JOURNEYS]

# ——— Argument Parsing ———

def parse_args():
    p = argparse.ArgumentParser(
        description="Session-based traffic simulator generating realistic user journeys."
    )
    p.add_argument("--target",  required=True,
                   help="Base URL of the site (e.g. https://example.com)")
    p.add_argument("--delay",   type=float, default=2.0,
                   help="Mean seconds between page requests within a journey (default: 2.0)")
    p.add_argument("--threads", type=int,   default=1,
                   help="Number of concurrent simulated users (default: 1)")
    return p.parse_args()

# ——— Helpers ———

def jitter(mean):
    """Gaussian delay around mean, floored at 0.5 s."""
    return max(0.5, random.gauss(mean, mean * 0.4))

# ——— Worker ———

def run_journeys():
    tid = threading.get_ident()
    while True:
        idx = random.choices(range(len(JOURNEYS)), weights=_WEIGHTS, k=1)[0]
        name  = _NAMES[idx]
        paths = _PATHS[idx]

        proxy_url = random.choice(proxies_list) if proxies_list else None
        proxy_cfg = {"http": proxy_url, "https": proxy_url} if proxy_url else {}
        ua = random.choice(UA_LIST)

        session = requests.Session()
        referer = None
        paths = [random.choice(PRODUCTS) if p == "PRODUCT" else p for p in paths]
        print(f"[»] Thread-{tid} journey={name} proxy={proxy_url or 'none'}")

        for path in paths:
            url = base + path
            headers = HEADERS_BASE.copy()
            headers["User-Agent"] = ua
            if referer:
                headers["Referer"] = referer

            try:
                print(f"  [→] {path}")
                r = session.get(url, headers=headers, timeout=15, proxies=proxy_cfg)
                r.raise_for_status()
                referer = url
            except requests.RequestException as e:
                print(f"  [!] {path} failed: {e}", file=sys.stderr)
                break

            time.sleep(jitter(args.delay))

        session.close()
        # Simulate think time between sessions (reading, distraction, etc.)
        time.sleep(jitter(args.delay * 4))

# ——— Main ———

if __name__ == "__main__":
    args = parse_args()
    base = args.target.rstrip("/")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    proxy_file = os.path.join(script_dir, "proxies.txt")
    proxies_list = []
    if os.path.isfile(proxy_file):
        try:
            with open(proxy_file) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    ip, port, user, pw = line.split(":", 3)
                    proxies_list.append(f"http://{user}:{pw}@{ip}:{port}")
        except Exception as e:
            print(f"[!] Could not load proxies.txt: {e}", file=sys.stderr)

    print(f"Starting: {base} | threads={args.threads} | delay~{args.delay}s | proxies={len(proxies_list)}")

    threads = []
    for _ in range(args.threads):
        t = threading.Thread(target=run_journeys, daemon=True)
        t.start()
        threads.append(t)

    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        print("\n[×] Shutting down…")
        sys.exit(0)

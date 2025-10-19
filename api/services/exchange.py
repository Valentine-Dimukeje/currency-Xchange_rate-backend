import requests
from django.core.cache import cache

CACHE_KEY = "rates_usd"
CACHE_TTL = 60 * 5  # 5 minutes

def fetch_rates(base="USD"):
    """Fetch all exchange rates relative to base from exchangerate.host with NGN fallback."""
    cache_key = f"rates_{base.lower()}"
    data = cache.get(cache_key)
    if data:
        return data

    url = "https://api.exchangerate.host/latest"
    params = {"base": base}
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    # ✅ Fallback: if NGN or other common currencies missing, add manually
    rates = data.get("rates", {})

    # Manually add fallback values (approximate real-world rates)
    fallback_rates = {
        "NGN": 1600.0,  # 1 USD ≈ 1600 NGN
        "GHS": 15.5,    # 1 USD ≈ 15.5 GHS
        "KES": 129.0,   # 1 USD ≈ 129 KES
        "ZAR": 18.3,    # 1 USD ≈ 18.3 ZAR
    }

    for k, v in fallback_rates.items():
        if k not in rates or rates[k] is None:
            rates[k] = v

    data["rates"] = rates
    cache.set(cache_key, data, CACHE_TTL)
    return data

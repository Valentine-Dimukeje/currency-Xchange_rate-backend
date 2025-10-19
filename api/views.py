from rest_framework.decorators import api_view
from rest_framework.response import Response
import requests
from django.core.cache import cache

# ✅ Fallback rates — used when live API fails or is missing currencies
FALLBACK_RATES = {
    "USD": 1.0,
    "EUR": 0.92,
    "GBP": 0.79,
    "NGN": 1470.0,  # ✅ Updated to latest real rate
    "GHS": 15.3,
    "ZAR": 18.1,
    "JPY": 150.0,
    "AUD": 1.52,
    "CAD": 1.37,
    "INR": 83.1,
    "KES": 129.0,
    "CNY": 7.2,
    "BRL": 5.65,
    "RUB": 93.0,
    "MXN": 18.2,
}


def fetch_rates():
    """
    Fetch live exchange rates (base USD) and merge with fallback data.
    Uses caching to reduce API calls and improve speed.
    """
    url = "https://open.er-api.com/v6/latest/USD"

    # ✅ Use cached data if available
    cached_data = cache.get("rates_usd")
    if cached_data:
        return cached_data

    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        data = res.json()

        if data.get("result") != "success":
            raise ValueError("Invalid API response")

        api_rates = data.get("rates", {})
    except Exception as e:
        print(f"⚠️ Failed to fetch live rates: {e}")
        api_rates = {}

    # ✅ Merge live and fallback rates
    merged_rates = {**FALLBACK_RATES, **api_rates}

    # Ensure every fallback currency is covered
    for code, val in FALLBACK_RATES.items():
        if code not in merged_rates or merged_rates[code] in (None, 0):
            merged_rates[code] = val

    result = {"base": "USD", "rates": merged_rates}

    # ✅ Cache the final merged result for 1 hour
    cache.set("rates_usd", result, timeout=3600)

    return result


@api_view(["GET"])
def rates(request):
    """Return all exchange rates relative to chosen base currency."""
    base = request.query_params.get("base", "USD").upper()
    data = fetch_rates()
    usd_rates = data["rates"]

    if base not in usd_rates:
        return Response({"error": f"Unsupported base currency: {base}"}, status=400)

    base_rate = usd_rates[base]
    converted = {c: (r / base_rate) for c, r in usd_rates.items() if r}

    return Response({
        "base": base,
        "rates": converted,
        "count": len(converted),
        "source": "live + fallback"
    })


@api_view(["GET"])
def convert(request):
    """Convert a given amount between two currencies."""
    from_currency = request.query_params.get("from", "").upper()
    to_currency = request.query_params.get("to", "").upper()
    amount = float(request.query_params.get("amount", 1))

    data = fetch_rates()
    usd_rates = data["rates"]

    if from_currency not in usd_rates or to_currency not in usd_rates:
        return Response(
            {"error": f"No rate available for {from_currency} → {to_currency}"},
            status=400
        )

    from_rate = usd_rates[from_currency]
    to_rate = usd_rates[to_currency]
    rate = to_rate / from_rate
    result = amount * rate

    return Response({
        "from": from_currency,
        "to": to_currency,
        "amount": amount,
        "rate": rate,
        "result": result,
        "source": "live + fallback"
    })

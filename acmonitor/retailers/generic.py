from __future__ import annotations
import json, logging, re
from datetime import datetime
from typing import Any
import requests
from bs4 import BeautifulSoup
from ..config import ProductConfig, ProductUrl
from ..models import StockResult

logger = logging.getLogger("acmonitor.retailers.generic")

IN_STOCK_TERMS = ["in stock", "available now", "add to basket", "add to cart", "buy now", "available for delivery"]
OUT_OF_STOCK_TERMS = ["out of stock", "sold out", "currently unavailable", "temporarily unavailable", "unavailable", "notify me", "email me when available", "coming soon"]
PRICE_RE = re.compile(r"£\s*([0-9]+(?:,[0-9]{3})*(?:\.[0-9]{1,2})?)")

def _json_ld_objects(soup: BeautifulSoup) -> list[dict[str, Any]]:
    objects = []
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        text = script.string or script.get_text(" ", strip=True)
        if not text:
            continue
        try:
            data = json.loads(text)
        except Exception:
            continue
        if isinstance(data, dict):
            objects.append(data)
            if isinstance(data.get("@graph"), list):
                objects.extend(x for x in data["@graph"] if isinstance(x, dict))
        elif isinstance(data, list):
            objects.extend(x for x in data if isinstance(x, dict))
    return objects

def _find_product_jsonld(soup: BeautifulSoup) -> dict[str, Any] | None:
    for obj in _json_ld_objects(soup):
        typ = obj.get("@type")
        if typ == "Product" or (isinstance(typ, list) and "Product" in typ):
            return obj
    return None

def _availability_from_jsonld(product: dict[str, Any]) -> tuple[bool | None, str]:
    offers = product.get("offers")
    if isinstance(offers, list):
        offers = offers[0] if offers else None
    if not isinstance(offers, dict):
        return None, ""
    availability = str(offers.get("availability", "")).lower()
    if "instock" in availability:
        return True, f"json-ld availability={availability}"
    if "outofstock" in availability or "soldout" in availability or "preorder" in availability:
        return False, f"json-ld availability={availability}"
    return None, f"json-ld availability={availability}" if availability else ""

def _price_from_jsonld(product: dict[str, Any]) -> float | None:
    offers = product.get("offers")
    if isinstance(offers, list):
        offers = offers[0] if offers else None
    if not isinstance(offers, dict):
        return None
    price = offers.get("price") or offers.get("lowPrice")
    if price is None:
        return None
    try:
        return float(str(price).replace(",", ""))
    except ValueError:
        return None

def _price_from_text(text: str) -> float | None:
    matches = PRICE_RE.findall(text or "")
    prices = []
    for m in matches:
        try:
            value = float(m.replace(",", ""))
            if 50 <= value <= 5000:
                prices.append(value)
        except ValueError:
            pass
    return min(prices) if prices else None

def _selected_text(soup: BeautifulSoup, selector: str | None) -> str:
    if not selector:
        return ""
    node = soup.select_one(selector)
    return node.get_text(" ", strip=True) if node else ""

def check_product_url(product: ProductConfig, product_url: ProductUrl, *, user_agent: str, timeout_seconds: int) -> StockResult:
    checked_at = datetime.now()
    headers = {"User-Agent": user_agent, "Accept-Language": "en-GB,en;q=0.9"}
    try:
        response = requests.get(product_url.url, headers=headers, timeout=timeout_seconds)
        response.raise_for_status()
    except Exception as exc:
        return StockResult(product.name, product_url.retailer, product_url.url, False, None, None, "request failed", checked_at, str(exc))

    soup = BeautifulSoup(response.text, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else None
    product_ld = _find_product_jsonld(soup)

    jsonld_availability = None
    jsonld_evidence = ""
    jsonld_price = None
    if product_ld:
        jsonld_availability, jsonld_evidence = _availability_from_jsonld(product_ld)
        jsonld_price = _price_from_jsonld(product_ld)

    selected_availability = _selected_text(soup, product_url.availability_selector)
    selected_price = _selected_text(soup, product_url.price_selector)
    visible_text = soup.get_text(" ", strip=True)
    combined = " ".join([selected_availability, visible_text[:50000]]).lower()

    if jsonld_availability is not None:
        available = jsonld_availability
        evidence = jsonld_evidence
    elif selected_availability:
        sl = selected_availability.lower()
        if any(t in sl for t in OUT_OF_STOCK_TERMS):
            available = False
            evidence = f"selector text: {selected_availability[:160]}"
        elif any(t in sl for t in IN_STOCK_TERMS):
            available = True
            evidence = f"selector text: {selected_availability[:160]}"
        else:
            available = False
            evidence = f"selector inconclusive: {selected_availability[:160]}"
    else:
        out_pos = min([combined.find(t) for t in OUT_OF_STOCK_TERMS if t in combined] or [10**9])
        in_pos = min([combined.find(t) for t in IN_STOCK_TERMS if t in combined] or [10**9])
        if out_pos < in_pos:
            available = False
            evidence = "matched out-of-stock phrase"
        elif in_pos < 10**9:
            available = True
            evidence = "matched in-stock phrase"
        else:
            available = False
            evidence = "no clear stock signal"

    price = jsonld_price or _price_from_text(selected_price) or _price_from_text(visible_text[:50000])
    return StockResult(product.name, product_url.retailer, product_url.url, available, price, title, evidence, checked_at)


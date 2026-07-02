from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any

import requests
from bs4 import BeautifulSoup

from ..config import ProductConfig, ProductUrl
from ..models import StockResult

logger = logging.getLogger("acmonitor.retailers.generic")
IN_STOCK_TERMS = ("in stock", "available now", "add to basket", "add to cart", "buy now", "available for delivery")
OUT_OF_STOCK_TERMS = ("out of stock", "sold out", "currently unavailable", "temporarily unavailable", "unavailable", "notify me", "email me when available", "coming soon")
PRICE_PATTERN = re.compile(r"£\s*([0-9]+(?:,[0-9]{3})*(?:\.[0-9]{1,2})?)")


def extract_price(text: str) -> float | None:
    prices = []
    for match in PRICE_PATTERN.findall(text or ""):
        try:
            value = float(match.replace(",", ""))
        except ValueError:
            continue
        if 0 < value <= 1_000_000:
            prices.append(value)
    return min(prices) if prices else None


def _json_ld_objects(soup: BeautifulSoup) -> list[dict[str, Any]]:
    objects = []
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        text = script.string or script.get_text(" ", strip=True)
        if not text:
            continue
        try:
            data = json.loads(text)
        except (json.JSONDecodeError, TypeError):
            continue
        candidates = data if isinstance(data, list) else [data]
        for candidate in candidates:
            if isinstance(candidate, dict):
                objects.append(candidate)
                graph = candidate.get("@graph")
                if isinstance(graph, list):
                    objects.extend(item for item in graph if isinstance(item, dict))
    return objects


def _find_product_jsonld(soup: BeautifulSoup) -> dict[str, Any] | None:
    for item in _json_ld_objects(soup):
        item_type = item.get("@type")
        if item_type == "Product" or (isinstance(item_type, list) and "Product" in item_type):
            return item
    return None


def _offers(product: dict[str, Any]) -> list[dict[str, Any]]:
    offers = product.get("offers")
    if isinstance(offers, dict):
        return [offers]
    if isinstance(offers, list):
        return [offer for offer in offers if isinstance(offer, dict)]
    return []


def _availability_from_jsonld(product: dict[str, Any]) -> tuple[bool | None, str]:
    values = [str(offer.get("availability", "")).lower() for offer in _offers(product)]
    if any("instock" in value for value in values):
        return True, "JSON-LD reports InStock"
    if any(token in value for value in values for token in ("outofstock", "soldout", "preorder")):
        return False, "JSON-LD reports unavailable"
    return None, ""


def _price_from_jsonld(product: dict[str, Any]) -> float | None:
    prices = []
    for offer in _offers(product):
        value = offer.get("price", offer.get("lowPrice"))
        try:
            if value is not None:
                prices.append(float(str(value).replace(",", "")))
        except ValueError:
            continue
    return min(prices) if prices else None


def _selected_text(soup: BeautifulSoup, selector: str | None) -> str:
    if not selector:
        return ""
    try:
        node = soup.select_one(selector)
    except Exception as exc:
        logger.warning("Invalid CSS selector %r: %s", selector, exc)
        return ""
    return node.get_text(" ", strip=True) if node else ""


def check_product_url(product: ProductConfig, product_url: ProductUrl, *, user_agent: str, timeout_seconds: int) -> StockResult:
    checked_at = datetime.now(timezone.utc)
    headers = {"User-Agent": user_agent, "Accept-Language": "en-GB,en;q=0.9"}
    try:
        response = requests.get(product_url.url, headers=headers, timeout=timeout_seconds)
        response.raise_for_status()
    except requests.RequestException as exc:
        return StockResult(product.name, product_url.retailer, product_url.url, False, None, None, "request failed", checked_at, str(exc))

    soup = BeautifulSoup(response.text, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else None
    product_data = _find_product_jsonld(soup)
    json_availability, json_evidence = _availability_from_jsonld(product_data) if product_data else (None, "")
    selected_availability = _selected_text(soup, product_url.availability_selector)
    selected_price = _selected_text(soup, product_url.price_selector)
    visible_text = soup.get_text(" ", strip=True)[:50_000]

    if json_availability is not None:
        available, evidence = json_availability, json_evidence
    elif selected_availability:
        selected_lower = selected_availability.lower()
        if any(term in selected_lower for term in OUT_OF_STOCK_TERMS):
            available, evidence = False, f"selector text: {selected_availability[:160]}"
        elif any(term in selected_lower for term in IN_STOCK_TERMS):
            available, evidence = True, f"selector text: {selected_availability[:160]}"
        else:
            available, evidence = False, f"selector inconclusive: {selected_availability[:160]}"
    else:
        page_lower = visible_text.lower()
        out_position = min((page_lower.find(term) for term in OUT_OF_STOCK_TERMS if term in page_lower), default=10**9)
        in_position = min((page_lower.find(term) for term in IN_STOCK_TERMS if term in page_lower), default=10**9)
        if out_position < in_position:
            available, evidence = False, "matched out-of-stock phrase"
        elif in_position < 10**9:
            available, evidence = True, "matched in-stock phrase"
        else:
            available, evidence = False, "no clear stock signal"

    price = (_price_from_jsonld(product_data) if product_data else None) or extract_price(selected_price) or extract_price(visible_text)
    return StockResult(product.name, product_url.retailer, product_url.url, available, price, title, evidence, checked_at)

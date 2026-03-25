import json
import logging
import urllib.parse

import requests
from bs4 import BeautifulSoup

from tracker import config
from tracker.models import Product
from tracker.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

BASE_URL = "https://www.elcorteingles.es"
SEARCH_URL = f"{BASE_URL}/supermercado/search/"


class ElCorteInglesScraper(BaseScraper):
    STORE_NAME = "El Corte Inglés"

    def scrape(self) -> list[Product]:
        try:
            return self._fetch()
        except Exception as e:
            logger.error(f"[{self.STORE_NAME}] Error inesperado: {e}", exc_info=True)
            return []

    def _fetch(self) -> list[Product]:
        session = requests.Session()
        session.headers.update(self.BASE_HEADERS)

        # Warm-up: obtener cookies de sesión antes de la búsqueda
        try:
            session.get(f"{BASE_URL}/supermercado/", timeout=15)
        except Exception:
            pass  # No es crítico

        query = urllib.parse.quote(config.QUERY)
        url = f"{SEARCH_URL}?s={query}"

        resp = session.get(url, timeout=20)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "lxml")

        # Estrategia 1: schema.org microdata (JSON-LD)
        products = self._parse_json_ld(soup, url)
        if products:
            logger.info(f"[{self.STORE_NAME}] {len(products)} productos (via JSON-LD)")
            return products

        # Estrategia 2: HTML
        products = self._parse_html(soup, url)
        logger.info(f"[{self.STORE_NAME}] {len(products)} productos (via HTML)")
        return products

    def _parse_json_ld(self, soup: BeautifulSoup, fallback_url: str) -> list[Product]:
        products = []
        scripts = soup.find_all("script", type="application/ld+json")

        for script in scripts:
            try:
                data = json.loads(script.string or "")
            except (json.JSONDecodeError, TypeError):
                continue

            items = []
            if data.get("@type") == "ItemList":
                items = [
                    el.get("item", el)
                    for el in data.get("itemListElement", [])
                ]
            elif data.get("@type") == "Product":
                items = [data]

            for item in items:
                try:
                    if item.get("@type") != "Product":
                        continue
                    name = item.get("name", "")
                    offers = item.get("offers", {})
                    price_raw = offers.get("price") or offers.get("lowPrice")
                    url = item.get("url", fallback_url)

                    if not name or price_raw is None:
                        continue

                    price = config.parse_price(str(price_raw))
                    if price:
                        products.append(Product(
                            store=self.STORE_NAME,
                            name=name,
                            price=price,
                            url=url,
                        ))
                except Exception as e:
                    logger.debug(f"[{self.STORE_NAME}] Error en item JSON-LD: {e}")

        return products

    def _parse_html(self, soup: BeautifulSoup, fallback_url: str) -> list[Product]:
        products = []

        cards = (
            soup.select(".c-product-tile")
            or soup.select("li[data-product-id]")
            or soup.select(".product-item")
            or soup.select("article[data-product]")
        )

        for card in cards:
            try:
                name_el = (
                    card.select_one(".c-product-tile__title-link")
                    or card.select_one(".c-product-tile__title")
                    or card.select_one("h3 a")
                    or card.select_one("h3")
                )
                price_el = (
                    card.select_one(".c-product-tile__price-current")
                    or card.select_one(".price-current")
                    or card.select_one("[class*='price']")
                )
                link_el = (
                    card.select_one("a.c-product-tile__title-link")
                    or card.select_one("a[href*='/supermercado/']")
                    or card.select_one("a[href]")
                )

                if not name_el or not price_el:
                    continue

                name = name_el.get_text(strip=True)
                price = config.parse_price(price_el.get_text(strip=True))
                href = link_el["href"] if link_el else fallback_url
                url = href if href.startswith("http") else f"{BASE_URL}{href}"

                if price:
                    products.append(Product(
                        store=self.STORE_NAME,
                        name=name,
                        price=price,
                        url=url,
                    ))
            except Exception as e:
                logger.debug(f"[{self.STORE_NAME}] Error parseando tarjeta HTML: {e}")

        return products

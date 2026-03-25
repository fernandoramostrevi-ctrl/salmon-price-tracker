import logging

import requests

from tracker import config
from tracker.models import Product
from tracker.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

# Categoría 36 = "Salazones y ahumados" — no requiere warehouse ni postal code
CATEGORY_URL = "https://tienda.mercadona.es/api/categories/36/?lang=es"
KEYWORDS = ["salmon", "salmón"]


class MercadonaScraper(BaseScraper):
    STORE_NAME = "Mercadona"

    def scrape(self) -> list[Product]:
        try:
            return self._fetch()
        except Exception as e:
            logger.error(f"[{self.STORE_NAME}] Error inesperado: {e}", exc_info=True)
            return []

    def _fetch(self) -> list[Product]:
        headers = {
            **self.BASE_HEADERS,
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://tienda.mercadona.es/",
            "Origin": "https://tienda.mercadona.es",
        }

        resp = requests.get(CATEGORY_URL, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        products = []
        # La categoría tiene subcategorías, cada una con productos
        for subcategory in data.get("categories", []):
            for item in subcategory.get("products", []):
                name = item.get("display_name", "")
                if not any(kw in name.lower() for kw in KEYWORDS):
                    continue

                pi = item.get("price_instructions", {})
                price = config.parse_price(str(pi.get("unit_price", "")))
                if price is None:
                    continue

                # reference_price es el precio por kg (reference_format = "kg")
                price_per_kg = config.parse_price(str(pi.get("reference_price", "")))

                products.append(Product(
                    store=self.STORE_NAME,
                    name=name,
                    price=price,
                    url=item.get("share_url", "https://tienda.mercadona.es"),
                    weight=item.get("packaging", ""),
                    price_per_kg=price_per_kg,
                ))

        logger.info(f"[{self.STORE_NAME}] {len(products)} productos encontrados")
        return products

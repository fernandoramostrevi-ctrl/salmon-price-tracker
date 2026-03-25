import logging
import urllib.parse

from tracker import config
from tracker.models import Product
from tracker.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

SEARCH_URL = "https://www.ahorramas.com/buscador"
BASE_URL = "https://www.ahorramas.com"
KEYWORDS = ["salmon", "salmón"]


class AhorramasScraper(BaseScraper):
    STORE_NAME = "Ahorramás"

    def scrape(self) -> list[Product]:
        try:
            return self._fetch()
        except Exception as e:
            logger.error(f"[{self.STORE_NAME}] Error inesperado: {e}", exc_info=True)
            return []

    def _fetch(self) -> list[Product]:
        from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

        query = urllib.parse.quote(config.QUERY)
        url = f"{SEARCH_URL}?q={query}"

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-blink-features=AutomationControlled",
                ],
            )
            context = browser.new_context(
                user_agent=self.BASE_HEADERS["User-Agent"],
                locale="es-ES",
                viewport={"width": 1280, "height": 800},
            )
            context.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
            page = context.new_page()

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=25_000)
                page.wait_for_selector(".product-tile", timeout=15_000)
            except PlaywrightTimeout:
                logger.warning(f"[{self.STORE_NAME}] Timeout esperando productos")
                browser.close()
                return []

            products = self._parse_products(page, url)
            browser.close()

        logger.info(f"[{self.STORE_NAME}] {len(products)} productos encontrados")
        return products

    def _parse_products(self, page, fallback_url: str) -> list[Product]:
        products = []
        cards = page.query_selector_all(".product-tile")

        for card in cards:
            try:
                # Nombre y URL desde el enlace del producto
                link_el = card.query_selector("a.product-pdp-link")
                if not link_el:
                    continue

                # El nombre está en data-creative (title y inner_text están vacíos)
                name = (
                    link_el.get_attribute("data-creative")
                    or link_el.get_attribute("title")
                    or link_el.inner_text().strip()
                )
                if not name or not any(kw in name.lower() for kw in KEYWORDS):
                    continue

                href = link_el.get_attribute("href") or fallback_url
                url = href if href.startswith("http") else f"{BASE_URL}{href}"

                price_el = card.query_selector(".sales")
                kg_el = card.query_selector(".unit-price-row")
                if not price_el:
                    continue

                price = config.parse_price(price_el.inner_text().strip())
                price_per_kg = config.parse_price(kg_el.inner_text().strip()) if kg_el else None

                if price and price < 500:
                    products.append(Product(
                        store=self.STORE_NAME,
                        name=name,
                        price=price,
                        url=url,
                        price_per_kg=price_per_kg,
                    ))
            except Exception as e:
                logger.debug(f"[{self.STORE_NAME}] Error parseando tarjeta: {e}")

        return products

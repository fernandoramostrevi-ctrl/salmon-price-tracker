import logging
import re
import urllib.parse

from tracker import config
from tracker.models import Product
from tracker.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

SEARCH_URL = "https://www.compraonline.alcampo.es/search"
BASE_URL = "https://www.compraonline.alcampo.es"
KEYWORDS = ["salmon", "salmón"]


class AlcampoScraper(BaseScraper):
    STORE_NAME = "Alcampo"

    def scrape(self) -> list[Product]:
        try:
            return self._fetch()
        except Exception as e:
            logger.error(f"[{self.STORE_NAME}] Error inesperado: {e}", exc_info=True)
            return []

    def _fetch(self) -> list[Product]:
        # Alcampo es una SPA React — requiere Playwright para renderizar
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

            products = []
            page = context.new_page()

            # Interceptar llamadas a la API interna para capturar los datos JSON
            api_products = []

            def handle_response(response):
                if "product" in response.url and response.status == 200:
                    try:
                        data = response.json()
                        self._extract_from_api(data, api_products)
                    except Exception:
                        pass

            page.on("response", handle_response)

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30_000)
                # Esperar a que carguen productos
                page.wait_for_selector(
                    ".product-card-container",
                    timeout=20_000,
                )
            except PlaywrightTimeout:
                logger.warning(f"[{self.STORE_NAME}] Timeout esperando productos")
                browser.close()
                return []

            # Si capturamos datos vía API, usarlos
            if api_products:
                browser.close()
                logger.info(f"[{self.STORE_NAME}] {len(api_products)} productos (via API intercept)")
                return api_products

            # Fallback: parsear el DOM renderizado
            products = self._parse_dom(page, url)
            browser.close()

        logger.info(f"[{self.STORE_NAME}] {len(products)} productos encontrados")
        return products

    def _extract_from_api(self, data: dict, products: list) -> None:
        items = (
            data.get("products") or data.get("results") or
            data.get("data", {}).get("products") or []
        )
        for item in items:
            name = item.get("name") or item.get("displayName") or item.get("title", "")
            if not any(kw in name.lower() for kw in KEYWORDS):
                continue
            price_val = (
                item.get("price", {}).get("value")
                if isinstance(item.get("price"), dict)
                else item.get("price")
            )
            if price_val is None:
                return
            price = config.parse_price(str(price_val))
            slug = item.get("url") or item.get("slug") or item.get("urlKey", "")
            url = slug if slug.startswith("http") else f"{BASE_URL}{slug}"
            if price:
                products.append(Product(
                    store=self.STORE_NAME,
                    name=name,
                    price=price,
                    url=url,
                ))

    def _parse_dom(self, page, fallback_url: str) -> list[Product]:
        products = []
        cards = page.query_selector_all(".product-card-container")
        for card in cards:
            try:
                link_el = card.query_selector("[data-test='fop-product-link']")
                # El precio unitario está en el primer [data-test*='price'] con euros
                price_els = card.query_selector_all("[data-test*='price']")

                if not link_el or not price_els:
                    continue

                name = link_el.inner_text().strip()
                if not any(kw in name.lower() for kw in KEYWORDS):
                    continue

                price = None
                price_per_kg = None
                for price_el in price_els:
                    text = price_el.inner_text().strip()
                    if "kilogramo" in text or "kilo" in text or "litro" in text:
                        # Este es el precio por kg
                        price_per_kg = config.parse_price(text)
                    else:
                        # Precio unitario del paquete
                        if price is None:
                            p = config.parse_price(text)
                            if p and p < 500:
                                price = p

                href = link_el.get_attribute("href") or fallback_url
                url = href if href.startswith("http") else f"{BASE_URL}{href}"

                if price:
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

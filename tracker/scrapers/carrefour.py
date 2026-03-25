import logging
import urllib.parse

from tracker import config
from tracker.models import Product
from tracker.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

SEARCH_URL = "https://www.carrefour.es/supermercado/search"
BASE_URL = "https://www.carrefour.es"
KEYWORDS = ["salmon", "salmón"]


class CarrefourScraper(BaseScraper):
    STORE_NAME = "Carrefour"

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
                extra_http_headers={"Accept-Language": "es-ES,es;q=0.9"},
            )
            context.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )

            # Interceptar llamadas API internas de Carrefour
            api_products = []

            def handle_response(response):
                url_lower = response.url.lower()
                if response.status == 200 and any(k in url_lower for k in ["search", "product", "catalog"]):
                    try:
                        ct = response.headers.get("content-type", "")
                        if "json" in ct:
                            data = response.json()
                            self._extract_from_api(data, api_products)
                    except Exception:
                        pass

            page = context.new_page()
            page.on("response", handle_response)

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30_000)
                # Esperar productos — varios selectores posibles
                page.wait_for_selector(
                    ".product-card, [data-testid='product-card'], .ebx-result, "
                    "article[class*='product'], [class*='ProductCard']",
                    timeout=20_000,
                )
            except PlaywrightTimeout:
                logger.warning(f"[{self.STORE_NAME}] Timeout esperando productos")
                browser.close()
                return []

            if api_products:
                browser.close()
                logger.info(f"[{self.STORE_NAME}] {len(api_products)} productos (via API intercept)")
                return api_products

            products = self._parse_dom(page, url)
            browser.close()

        logger.info(f"[{self.STORE_NAME}] {len(products)} productos encontrados")
        return products

    def _extract_from_api(self, data, products: list) -> None:
        # Carrefour Empathy/Elasticsearch response
        items = (
            data.get("catalog", {}).get("content", [])
            or data.get("results", [])
            or data.get("products", [])
            or data.get("data", {}).get("products", [])
        )
        for item in items:
            name = (
                item.get("name") or item.get("displayName")
                or item.get("title") or item.get("description", "")
            )
            if not name or not any(kw in name.lower() for kw in KEYWORDS):
                continue

            # Precio puede estar en varias rutas
            price_val = (
                item.get("price", {}).get("value")
                if isinstance(item.get("price"), dict)
                else item.get("price")
                or item.get("priceValue")
                or item.get("salePrice")
            )
            if price_val is None:
                continue

            price = config.parse_price(str(price_val))
            url = item.get("url") or item.get("link") or item.get("productUrl", "")
            if url and not url.startswith("http"):
                url = f"{BASE_URL}{url}"

            if price:
                products.append(Product(
                    store=self.STORE_NAME,
                    name=name,
                    price=price,
                    url=url or f"{SEARCH_URL}?q={urllib.parse.quote(config.QUERY)}",
                ))

    def _parse_dom(self, page, fallback_url: str) -> list[Product]:
        products = []
        cards = page.query_selector_all(
            ".product-card, [data-testid='product-card'], .ebx-result, "
            "article[class*='product'], li[class*='ProductCard']"
        )
        for card in cards:
            try:
                name_el = (
                    card.query_selector(".product-card__title")
                    or card.query_selector("[data-testid='product-name']")
                    or card.query_selector("h3")
                    or card.query_selector("[class*='title']")
                )
                price_el = (
                    card.query_selector(".product-card__price")
                    or card.query_selector("[data-testid='product-price']")
                    or card.query_selector("[class*='price']")
                )
                link_el = card.query_selector("a[href]")

                if not name_el or not price_el:
                    continue

                name = name_el.inner_text().strip()
                if not any(kw in name.lower() for kw in KEYWORDS):
                    continue

                price = config.parse_price(price_el.inner_text().strip())
                href = link_el.get_attribute("href") if link_el else fallback_url
                url = href if href.startswith("http") else f"{BASE_URL}{href}"

                if price:
                    products.append(Product(
                        store=self.STORE_NAME,
                        name=name,
                        price=price,
                        url=url,
                    ))
            except Exception as e:
                logger.debug(f"[{self.STORE_NAME}] Error parseando tarjeta: {e}")

        return products

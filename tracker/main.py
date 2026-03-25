"""
Punto de entrada del tracker.
Ejecuta todos los scrapers, filtra por rango de precio y envía email si hay resultados.
"""
import logging
import sys

from tracker import config
from tracker.models import Product
from tracker.notifier import send_alert
from tracker.scrapers.mercadona import MercadonaScraper
from tracker.scrapers.alcampo import AlcampoScraper
from tracker.scrapers.ahorramas import AhorramasScraper

logger = logging.getLogger(__name__)

SCRAPERS = [
    MercadonaScraper,
    AlcampoScraper,
    AhorramasScraper,
]


def main() -> int:
    config.setup_logging()
    logger.info(
        f"Iniciando búsqueda de '{config.QUERY}' "
        f"(precio/kg ≤ {config.PRICE_MAX:.2f}€)"
    )

    all_products: list[Product] = []

    for ScraperClass in SCRAPERS:
        scraper = ScraperClass()
        logger.info(f"Scraping {scraper.STORE_NAME}...")
        results = scraper.scrape()
        all_products.extend(results)
        logger.info(f"  → {len(results)} productos encontrados en {scraper.STORE_NAME}")

    logger.info(f"Total productos encontrados: {len(all_products)}")

    # Filtrar por precio por kg. Si no hay dato de kg, descartar el producto.
    in_range = [
        p for p in all_products
        if p.price_per_kg is not None and p.price_per_kg <= config.PRICE_MAX
    ]

    logger.info(f"Productos con precio/kg ≤ {config.PRICE_MAX:.2f}€: {len(in_range)}")

    if in_range:
        for p in in_range:
            logger.info(f"  ✓ {p}")
        send_alert(in_range)
        return 0
    else:
        logger.info("Sin resultados en el rango de precio. No se envía email.")
        return 0


if __name__ == "__main__":
    sys.exit(main())

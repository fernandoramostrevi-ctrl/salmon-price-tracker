from abc import ABC, abstractmethod
from tracker.models import Product


class BaseScraper(ABC):
    STORE_NAME: str = ""

    # Headers comunes para parecer un navegador real
    BASE_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) "
            "Gecko/20100101 Firefox/125.0"
        ),
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    @abstractmethod
    def scrape(self) -> list[Product]:
        """
        Devuelve lista de productos encontrados.
        NUNCA lanza excepciones — las captura internamente y devuelve [].
        """
        ...

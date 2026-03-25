from dataclasses import dataclass, field


@dataclass
class Product:
    store: str
    name: str
    price: float        # precio del paquete/unidad
    url: str
    weight: str = field(default="")
    price_per_kg: float | None = field(default=None)  # precio por kilogramo

    def __str__(self) -> str:
        weight_str = f" ({self.weight})" if self.weight else ""
        pkg = f"{self.price:.2f}€"
        kg = f" [{self.price_per_kg:.2f}€/kg]" if self.price_per_kg else ""
        return f"{self.store}: {self.name}{weight_str} — {pkg}{kg}"

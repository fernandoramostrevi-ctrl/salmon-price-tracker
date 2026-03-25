# 🐟 Salmon Price Tracker

Sistema automatizado de monitoreo de precios de salmón en supermercados españoles con notificaciones por email.

## 📋 Descripción

Este proyecto rastrea automáticamente los precios del salmón en tres supermercados españoles:
- **Mercadona** (API)
- **Alcampo** (Web scraping)
- **Ahorramás** (Web scraping)

Cuando detecta precios por debajo de un umbral configurado, envía un email automático con los detalles de la oferta.

## 🚀 Características

- ✅ Scraping automatizado de 3 supermercados
- ✅ Ejecución programada diaria (cron)
- ✅ Notificaciones por email vía Gmail
- ✅ Logging completo de todas las ejecuciones
- ✅ Manejo robusto de errores
- ✅ Configuración mediante variables de entorno

## 🛠️ Tecnologías

- **Python 3.11+**
- **Playwright** - Para web scraping dinámico
- **Requests** - Para APIs REST
- **BeautifulSoup4** - Para parsing HTML
- **Gmail API** - Para envío de notificaciones

## 📦 Instalación

### 1. Clonar el repositorio
```bash
git clone https://github.com/fernandoramostrevi-ctrl/salmon-price-tracker.git
cd salmon-price-tracker
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
playwright install chromium
```

### 3. Configurar credenciales

Copia el archivo de ejemplo y configura tus credenciales:
```bash
cp .env.example .env
nano .env
```

Completa las siguientes variables:
```env
# Credenciales Gmail
GMAIL_ADDRESS=tu-email@gmail.com
GMAIL_APP_PASSWORD=tu-app-password-16-caracteres

# Umbrales de precio (€/kg)
MERCADONA_THRESHOLD=12.99
ALCAMPO_THRESHOLD=11.99
AHORRAMAS_THRESHOLD=10.99
```

### 4. Obtener App Password de Gmail

1. Ve a https://myaccount.google.com/apppasswords
2. Selecciona "Mail" y "Other device"
3. Copia la contraseña de 16 caracteres
4. Pégala en `GMAIL_APP_PASSWORD`

## 🎯 Uso

### Ejecución manual
```bash
cd /root/salmon-tracker
./run_tracker.sh
```

### Ejecución automática (cron)

El proyecto incluye configuración para ejecutarse diariamente a las 9:00 AM:
```bash
# Instalar el cron job
crontab crontab.txt

# Verificar que está instalado
crontab -l
```

### Ver logs
```bash
# Log de la aplicación
tail -f logs/tracker.log

# Log del cron
tail -f logs/cron.log
```

## 📁 Estructura del proyecto
```
salmon-tracker/
├── tracker/
│   ├── main.py              # Orquestador principal
│   ├── config.py            # Configuración y utilidades
│   ├── notifier.py          # Envío de emails
│   └── scrapers/
│       ├── mercadona.py     # Scraper Mercadona (API)
│       ├── alcampo.py       # Scraper Alcampo (Playwright)
│       └── ahorramas.py     # Scraper Ahorramás (Playwright)
├── logs/                    # Logs de ejecución
├── .env                     # Credenciales (NO incluido en git)
├── .env.example             # Plantilla de configuración
├── requirements.txt         # Dependencias Python
├── run_tracker.sh           # Script de ejecución
└── crontab.txt              # Configuración cron
```

## 🔐 Seguridad

- ⚠️ **Nunca** subas el archivo `.env` a GitHub
- ✅ El `.gitignore` ya está configurado para protegerlo
- ✅ Usa Gmail App Passwords, no tu contraseña real
- ✅ Los logs no contienen información sensible

## 📧 Formato del email de notificación

Cuando se detecta una oferta, recibes un email con:
- Nombre del supermercado
- Precio actual (€/kg)
- Umbral configurado
- Enlace directo al producto

## 🐛 Troubleshooting

### No recibo emails

1. Verifica que `GMAIL_APP_PASSWORD` sea correcto
2. Comprueba que la autenticación en dos pasos esté activada en Gmail
3. Revisa los logs: `tail -f logs/tracker.log`

### Errores de scraping

Los supermercados pueden cambiar su estructura web. Si un scraper falla:
1. Revisa los logs para identificar el error
2. Verifica que Playwright esté instalado: `playwright install chromium`
3. Los scrapers están diseñados para fallar de forma segura (continúan con otros supermercados)

### El cron no se ejecuta

1. Verifica que esté instalado: `crontab -l`
2. Revisa logs de cron: `tail -f logs/cron.log`
3. Asegúrate de que las rutas en `crontab.txt` sean absolutas

## 🔄 Próximas mejoras

- [ ] Interfaz web para visualizar histórico de precios
- [ ] Soporte para más supermercados (Carrefour, Lidl, etc.)
- [ ] Notificaciones por Telegram/WhatsApp
- [ ] Dashboard con gráficos de evolución de precios
- [ ] Base de datos para almacenar histórico

## 📝 Licencia

Este proyecto es de uso personal. Si lo usas, por favor respeta los términos de servicio de los supermercados.

## 👤 Autor

**Fernando Ramos**

---

⭐ Si te resulta útil, ¡dale una estrella al repositorio!

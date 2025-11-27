# Energy Tariff Frontend

Ein modernes Vue.js Frontend für den Vergleich von Energietarifen.

## Features

- 🔍 **Tarifvergleich**: Vergleichen Sie Stromtarife basierend auf Ihrem Verbrauch
- 📊 **Marktdaten**: Aktuelle Strompreise und Marktentwicklungen
- 💡 **Spartipps**: Interaktive Tipps zum Energiesparen mit Sparpotenzial-Rechner
- 📱 **Responsive Design**: Optimiert für Desktop und Mobile
- ⚡ **Schnell**: Aufgebaut mit Vite für optimale Performance

## Technologien

- **Vue.js 3** - Composition API
- **Vue Router** - Client-side Routing
- **Chart.js** - Datenvisualisierung
- **Axios** - HTTP Client
- **Vite** - Build Tool
- **Font Awesome** - Icons

## Installation

1. Dependencies installieren:
```bash
cd frontend
npm install
```

2. Development Server starten:
```bash
npm run dev
```

3. Für Production builden:
```bash
npm run build
```

## Verwendung

### Development
```bash
npm run dev
```
Das Frontend läuft auf `http://localhost:3000` und proxied API-Calls zu `http://localhost:8000`.

### Production
```bash
npm run build
npm run preview
```

## API Integration

Das Frontend kommuniziert mit dem FastAPI Backend über:
- `/api/calculate` - Tarifberechnung
- `/api/market-prices` - Marktdaten
- `/api/usage-tips` - Spartipps

Die API-Konfiguration befindet sich in `src/services/api.js`.

## Komponenten

### Views
- **Home** - Startseite mit Hero-Section und Schnellrechner
- **TariffComparison** - Hauptvergleichsseite mit Formularen und Ergebnissen
- **MarketData** - Marktdaten mit interaktiven Charts
- **SavingsTips** - Spartipps mit Sparpotenzial-Rechner

### Components
- **Header** - Navigation mit responsive Mobile-Menu
- **Footer** - Footer mit Links und Informationen

## Styling

Das Frontend verwendet ein maßgeschneidertes CSS-Framework mit:
- Utility-First Ansatz
- Responsive Grid System
- Konsistente Design Tokens
- Smooth Animations

## Browser Support

- Chrome/Chromium 88+
- Firefox 85+
- Safari 14+
- Edge 88+

## Entwicklung

### Ordnerstruktur
```
src/
├── components/     # Wiederverwendbare Komponenten
├── views/         # Seiten-Komponenten
├── services/      # API und Business Logic
├── style.css      # Globale Styles
├── main.js        # App Entry Point
└── App.vue        # Root Component
```

### Code Style
- Vue 3 Composition API
- Single File Components
- Scoped CSS
- ESLint Konfiguration

## Deployment

1. Build erstellen:
```bash
npm run build
```

2. `dist/` Ordner auf Webserver deployen

3. Nginx/Apache für SPA-Routing konfigurieren

## Umgebungsvariablen

Erstellen Sie eine `.env` Datei:
```
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_NAME=Energy Tariff Comparison
```

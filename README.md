# DYNERGY - Energy Tariff Comparison Platform 🔋

A comprehensive web application for comparing dynamic and fixed energy tariffs in Germany, helping consumers make informed decisions about their electricity contracts.

## 📋 Project Overview

This university project provides an intelligent platform that:
- Compares dynamic vs. fixed electricity tariffs
- Analyzes consumption patterns and forecasts future usage
- Calculates potential savings with dynamic tariffs
- Provides risk analysis and backtesting capabilities
- Integrates real-time German energy market data

## 🏗️ Architecture

The application consists of two main components:
- **Backend**: FastAPI (Python 3.11) - REST API and data processing
- **Frontend**: Vue.js 3 with Vite - Modern, responsive UI

## 🐳 Quick Start with Docker (Recommended)

### Prerequisites
- Docker Desktop installed ([Download here](https://www.docker.com/products/docker-desktop))
- 4GB RAM minimum
- 5GB free disk space

### Running the Application

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd Project_Energy_Tariffs
   ```

2. **Start with Docker Compose**
   ```bash
   docker-compose up --build
   ```

3. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

4. **Stop the application**
   ```bash
   docker-compose down
   ```

### Docker Commands

```bash
# Start in detached mode (background)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop containers
docker-compose down

# Remove containers and volumes
docker-compose down -v

# Rebuild after changes
docker-compose up --build
```

## 💻 Local Development Setup

If you prefer running without Docker:

### Prerequisites
- Python 3.11+
- Node.js 18+
- npm or yarn

### Installation

1. **Install Python dependencies**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Install Node.js dependencies**
   ```bash
   cd src/frontend
   npm install
   cd ../..
   ```

### Running Locally

**Option 1: Use the startup script**
```bash
chmod +x start.sh
./start.sh
```

**Option 2: Run manually**

Terminal 1 - Backend:
```bash
source venv/bin/activate
python app.py
```

Terminal 2 - Frontend:
```bash
cd src/frontend
npm run dev
```

## 📁 Project Structure

```
.
├── app.py                      # FastAPI main application
├── requirements.txt            # Python dependencies
├── docker-compose.yml          # Docker orchestration
├── Dockerfile.backend          # Backend container
├── Dockerfile.frontend         # Frontend container
├── nginx.conf                  # Nginx configuration
├── src/
│   ├── backend/               # Backend logic
│   │   ├── energy_tariff.py   # Tariff models
│   │   ├── forecasting/       # Usage prediction
│   │   └── scrapers/          # Price data scrapers
│   └── frontend/              # Vue.js application
│       ├── src/
│       │   ├── components/    # Vue components
│       │   ├── views/         # Page views
│       │   └── main.js        # App entry point
│       └── package.json
├── app_data/                  # Market data & forecasts
├── data/                      # Analysis data
└── analysis/                  # Jupyter notebooks & tests
```

## 🔧 Key Features

### Backend Features
- RESTful API with FastAPI
- Energy consumption forecasting (Prophet, Chronos)
- Standard Load Profile (SLP) generation
- Risk analysis and backtesting
- Web scraping for current tariff data (EnBW, Tibber)
- Historical price data integration

### Frontend Features
- Interactive tariff comparison
- Real-time price charts
- Usage pattern visualization
- Risk assessment dashboard
- Responsive design
- File upload for smart meter data

## 🧪 Testing

```bash
# Run backend tests
pytest analysis/test_*.py

# Run specific test
pytest analysis/test_tariff_calculation.py -v
```

## 📊 Data Sources

- German day-ahead market prices (ENTSO-E)
- Standard Load Profiles (BDEW)
- Energy provider APIs (EnBW, Tibber)
- Smart meter data (CSV upload)

## 🛠️ Technology Stack

### Backend
- FastAPI - Modern Python web framework
- Pandas - Data manipulation
- Prophet / Chronos - Time series forecasting
- Scikit-learn - Machine learning
- Selenium - Web scraping

### Frontend
- Vue.js 3 - Progressive JavaScript framework
- Chart.js - Interactive charts
- Axios - HTTP client
- Vite - Build tool

### DevOps
- Docker & Docker Compose
- Nginx - Web server
- uvicorn - ASGI server

## 📝 API Documentation

Once the application is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🎓 Academic Context

This project was developed as part of a university course. It demonstrates:
- Full-stack web development
- Machine learning for time series forecasting
- Data visualization
- RESTful API design
- Containerization and deployment

## 📄 License

See [LICENSE](LICENSE) file for details.

## 🤝 Contributing

This is an academic project. If you're a fellow student or interested in contributing, please:
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 👨‍💻 Author

Julius Becker - University Project 2025

## 🙏 Acknowledgments

- German energy market data providers
- Open-source forecasting libraries
- Course instructors and peers

---

**Note**: This is an educational project. Use the tariff calculations as guidance only. Always verify with official provider information before making decisions.
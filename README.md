# DYNERGY - Energy Tariff Comparison Platform

A comprehensive web application for comparing dynamic and fixed energy tariffs in Germany, helping consumers make informed decisions about their electricity contracts.

## Documentation

View the documentation on readthedocs
https://project-energy-tariffs.readthedocs.io/en/latest/index.html

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

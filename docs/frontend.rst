Frontend Architecture and User Interface
========================================

Overview
--------

The DYNERGY frontend is a Vue.js 3 Single Page Application (SPA) providing an intuitive interface for comparing energy tariffs. The application follows a user-centered design approach, ensuring accessibility for both technical and non-technical users.

The architecture emphasizes responsive design, accessibility compliance, and performance optimization across all devices.

Application Views
-----------------

Home.vue - Landing Page and User Onboarding
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The landing page serves as the primary entry point, featuring a hero section that communicates the application's value proposition and guides users toward action.

Key Features:
  - Hero section with call-to-action messaging
  - 3-step process guide (data entry, analysis, decision)
  - Statistics overview (2-minute comparison, free service)
  - Responsive design for all device types
  - Mobile-first approach

TariffComparison.vue - Core Comparison Functionality
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The core comparison page where users analyze electricity tariffs based on their consumption patterns. Accommodates both smart meter users and manual data entry.

Smart Meter Integration:
  - Drag-and-drop CSV upload interface
  - File validation and data preview
  - Support for 15-minute interval data formats

Manual Data Entry:
  - Annual consumption, household type, postal code input
  - Accessible design for all user skill levels

Results and Analysis:
  - Interactive comparison tables with cost breakdowns
  - Savings visualization vs. current tariff
  - Algorithm-based recommendations
  - Interactive charts for price evolution and consumption
  - Price forecasting functionality (see `price_forecasting.rst`_)

.. _price_forecasting.rst: price_forecasting.rst

ElectricityPriceInfo.vue - Educational Content and Price Transparency
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Educational page explaining electricity pricing complexity to help users make informed decisions.

Educational Components:
  - Distinction between consumption costs (ct/kWh) and fixed charges (€/month)
  - Price component breakdown (taxes 25%, grid 32%, energy procurement 43%)
  - Interactive expandable cards with detailed explanations
  - Tip boxes for energy savers and heavy consumers
  - Linear vs. traditional tariff model comparisons

SavingsTips.vue - Practical Energy Efficiency Guidance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Energy saving tips page providing actionable advice for reducing energy consumption.

Feature Set:
  - Categorized tips (heating/cooling, appliances, lighting, hot water, smart home)
  - Dynamic filtering with real-time updates
  - Tip cards with difficulty level (Easy/Medium/Hard)
  - Savings potential in Euro amounts and percentages
  - Implementation timeframes and step-by-step instructions
  - Tool and material checklists

Technical Architecture
----------------------

Design Principles
~~~~~~~~~~~~~~~~~

- **Mobile-First Design**: Responsive breakpoints at 768px (tablet) and 1024px (desktop)
- **Accessibility**: WCAG 2.1 compliant with semantic HTML and keyboard navigation
- **Performance**: Lazy loading, code splitting, and caching strategies
- **User Experience**: Intuitive navigation and progressive disclosure

Technology Stack
~~~~~~~~~~~~~~~~

- **Vue.js 3 Composition API**: Modern component architecture
- **Chart.js**: High-performance data visualization
- **Vite**: Bundle optimization and code splitting
- **Axios**: Reliable API communication with error handling




# Cyber-Safety Dark Pattern & Hidden Fee Detector

A consumer reporting portal that empowers users to identify, report, and validate deceptive e-commerce practices, specifically targeting subscription traps and hidden recurring fees.

## 🎯 Problem Statement Alignment

E-commerce sites and subscription services often trick users into paying extra through deceptive UI designs, sneaky prechecked boxes, and hidden recurring fees. Our solution directly tackles this challenge by creating a **consumer reporting portal** where users can:
- Submit suspicious websites or screenshots of deceptive layouts.
- Receive immediate AI-driven analysis of the dark patterns present, explicitly highlighting **financial impact** and recurring subscription traps.
- Participate in a community-voted index, democratizing cyber-safety and warning others about unethical web layouts.

## 🚀 Key Technologies & Features

### Google Services Usage
- **Multimodal Gemini API**: Powers the core detection engine, analyzing both text (URLs) and images (screenshots) to identify complex dark patterns like Forced Continuity and Misdirection.
- **Antigravity AI**: Extensively utilized for orchestrating the backend architecture, ensuring a highly scalable, robust, and clean foundation.

### Frontend UI/UX & Accessibility
- **Next.js & React**: A lightning-fast, accessible single-page application.
- **shadcn/ui & Tailwind CSS**: Premium, highly accessible UI components providing a native-like experience.
- **ReactBits**: Interactive data visualizations for clearly communicating risk scores and community consensus.

### Code Quality, Efficiency & Security
- **Strictly Typed**: Built with Pydantic and FastAPI, ensuring type safety from the database layer to the API boundaries.
- **High Efficiency**: Fully asynchronous endpoints (`async def`) ensuring non-blocking operations for high throughput.
- **Security-First**: 
  - Standard security headers enforced via custom FastAPI middleware (Strict-Transport-Security, X-Frame-Options, X-Content-Type-Options, X-XSS-Protection).
  - Secure environment variable management (no hardcoded credentials).
  - Strict CORS configuration limited to explicit origins.
- **Extensively Tested**: 100% passing test suite for core API flows using Pytest, with zero deprecation warnings.

---

## 🛠️ Quick Start Guide

Follow these simple steps to run the complete stack locally.

### 1. Prerequisites
- Python 3.10+
- Node.js 18+

### 2. Backend Setup

Open a terminal in the project root:

```bash
# Navigate to backend
cd backend

# Create and activate virtual environment (Windows)
python -m venv venv
venv\Scripts\activate
# For Mac/Linux: source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
```

**CRITICAL:** Open `backend/.env` and add your Gemini API Key:
```env
GEMINI_API_KEY=your_actual_key_here
```

```bash
# Seed the database with initial reports
python -m database.seed

# Start the FastAPI server
cd ..
uvicorn backend.main:app --reload
```
*The backend is now running at `http://localhost:8000`*

### 3. Frontend Setup

Open a **new** terminal in the project root:

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```
*The frontend is now running at `http://localhost:3000`*

---

## 🧪 Running Tests

To run the backend test suite:

```bash
# From the project root (ensure virtual environment is active)
pytest tests/test_api.py
```

## 🏗️ Architecture

- **Backend**: FastAPI, SQLAlchemy (SQLite), Pydantic, Multimodal Gemini API.
- **Frontend**: Next.js, Tailwind CSS, shadcn/ui.
- **Database**: SQLite (swap-ready for PostgreSQL).

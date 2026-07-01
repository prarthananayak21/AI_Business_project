# FinSight AI

## Competitive Analysis of Organizations in the Data Science and Artificial Intelligence Industry Using Real-Time Data Collection, Quantitative Analytics, Ecosystem Analysis, and AI-Based Business Intelligence

---

## Overview

FinSight AI is a Business Intelligence platform designed to analyze organizations in the Data Science and Artificial Intelligence industry. The system integrates real-time financial data, AI-powered business intelligence, quantitative analysis, and executive-level insights to support business decision-making.

The platform enables users to analyze companies, monitor live market trends, generate executive summaries, and interact with an AI-powered chatbot through a single dashboard.

---

## Features

### 🤖 AI Business Assistant
- Company-specific chatbot
- Business intelligence queries
- Company profile analysis
- Revenue information
- Corporate insights

### 📊 Live Market Momentum
- Real-time stock prices
- Historical market analysis
- RSI (Relative Strength Index)
- SMA (Simple Moving Average)
- Interactive price trend charts

### 🏢 Company Analyzer
- Company overview
- Industry details
- Revenue analysis
- Employee information
- Market position
- Business insights

### 📈 Dashboard Analytics
- KPI metrics
- Interactive visualizations
- Revenue trends
- Financial dashboards

### 💼 Executive Summary Generator
- NLP-based business summarization
- Key event extraction
- Business impact analysis
- Future outlook generation

### 💬 Chat Management
- Save chat history
- Rename chats
- Delete chats
- MySQL database integration

---

## Project Architecture

```
User
   │
   ▼
Streamlit Interface
   │
   ├───────────────┐
   │               │
   ▼               ▼

yFinance      Groq Llama 3.1
   │               │
   ▼               ▼

Financial Data   NLP & AI Processing

        │
        ▼

Business Intelligence Engine

        │
        ▼

Dashboard | Company Analyzer | Executive Summary | Chatbot
```

---

## Technologies Used

### Frontend
- Streamlit

### Backend
- Python

### Database
- MySQL

### AI Model
- Groq API
- Llama 3.1

### Data Collection
- yFinance

### Data Processing
- Pandas
- NumPy

### Visualization
- Plotly

### Environment
- VS Code

---

## Libraries Used

```
streamlit
groq
python-dotenv
mysql-connector-python
pandas
numpy
plotly
yfinance
```

---

## Data Sources

### Yahoo Finance (yFinance)

Used for:

- Live Stock Prices
- Historical Market Data
- Revenue Information
- Employee Count
- Company Financial Information

### Groq API

Used for:

- AI Chatbot
- Executive Summary Generation
- Company Information
- Query Understanding
- Business Insights

---

## Quantitative Analysis

The project performs quantitative analysis using:

- Revenue Analysis
- Market Trend Analysis
- Relative Strength Index (RSI)
- Simple Moving Average (SMA)
- Historical Price Analysis

---

## NLP Features

The project uses Large Language Models (Llama 3.1 via Groq) for:

- Natural Language Understanding
- Executive Summary Generation
- Business Insight Generation
- Company Query Analysis

---

## Workflow

1. User enters company name or query.
2. Company data is collected from Yahoo Finance.
3. Financial data is processed using Pandas and NumPy.
4. Technical indicators (RSI and SMA) are calculated.
5. AI model generates company insights and executive summaries.
6. Results are displayed through an interactive dashboard.

---

## Installation

### Clone the repository

```bash
git clone https://github.com/yourusername/FinSightAI.git
```

---

### Navigate to the project

```bash
cd FinSightAI
```

---

### Create Virtual Environment

```bash
python -m venv venv
```

Activate the environment.

Windows

```bash
venv\Scripts\activate
```

---

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

### Configure Environment Variables

Create a `.env` file.

```
GROQ_API_KEY=your_groq_api_key
```

---

### Configure MySQL

Update the database credentials in `app.py`.

```python
host="localhost"
user="root"
password="your_password"
```

---

### Run the Application

```bash
streamlit run app.py
```

---

## Folder Structure

```
FinSightAI/

│── app.py
│── database.py
│── requirements.txt
│── .env

│── pages
│     ├── Dashboard.py
│     └── Company_Explorer.py

│── utils
│     ├── executive_summary.py
│     ├── dna_score.py
│     ├── news_sentiment.py
│     ├── grounding.py
│     └── competitor_battle.py

│── assets

│── README.md
```

---

## Future Enhancements

- Machine Learning-based Stock Prediction
- News Sentiment Analysis
- Competitor Ranking
- Predictive Analytics
- Advanced Financial Dashboards
- Automated Report Generation

---

## Applications

- Business Intelligence
- Market Research
- Competitive Analysis
- Financial Analytics
- Investment Research
- AI Industry Monitoring

---

## Authors

**Prarthana P. Nayak**

Department of Computer Science and Engineering (Data Science)

---

## License

This project is developed for academic and educational purposes.

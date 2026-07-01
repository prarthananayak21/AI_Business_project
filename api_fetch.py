import yfinance as yf
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# -------------------------------
# GET TICKER USING AI (STRICT)
# -------------------------------
def get_ticker_from_ai(company_name):
    try:
        prompt = f"""
        Give ONLY the stock ticker of {company_name}.

        Rules:
        - If NOT publicly listed → return NONE
        - Do NOT guess
        """

        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant"
        )

        ticker = response.choices[0].message.content.strip().upper()

        if ticker == "NONE":
            return None

        return ticker

    except:
        return None


# -------------------------------
# GET COMPANY INFO
# -------------------------------
def get_company_info(company_name):
    ticker = get_ticker_from_ai(company_name)

    if not ticker:
        return None

    try:
        company = yf.Ticker(ticker)
        info = company.get_info()

        if not info or info.get("longName") is None:
            return None

        # Validate correct company
        if company_name.lower() not in info.get("longName", "").lower():
            return None

        return {
            "name": info.get("longName"),
            "ticker": ticker,
            "industry": info.get("industry"),
            "country": info.get("country"),
            "market_cap": info.get("marketCap"),
            "revenue": info.get("totalRevenue"),
            "description": info.get("longBusinessSummary")
        }

    except:
        return None


# -------------------------------
# AI FALLBACK
# -------------------------------
def get_company_ai_info(company_name):
    try:
        prompt = f"""
        Give latest 2026 information about {company_name}.

        Include:
        - Industry
        - What they do
        - Revenue (approximate)
        - Growth trends
        - Key services

        Do NOT say cutoff knowledge.
        """

        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a business analyst."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.1-8b-instant"
        )

        return response.choices[0].message.content

    except:
        return "No info available"


# -------------------------------
# MULTI COMPANY DETECTION
# -------------------------------
def extract_companies(prompt):
    prompt = prompt.lower()
    words = prompt.replace(",", "").split()

    ignore = ["compare", "and", "vs", "with"]
    companies = [w for w in words if w not in ignore]

    return list(set(companies))


# -------------------------------
# AI COMPARISON INSIGHT
# -------------------------------
def get_comparison_insight(companies):
    try:
        prompt = f"""
        Compare the companies: {', '.join(companies)}.

        Give:
        - Growth comparison
        - Market position
        - Key differences
        """

        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant"
        )

        return response.choices[0].message.content

    except:
        return "No insight available"
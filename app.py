import streamlit as st
import os
from groq import Groq
from dotenv import load_dotenv
import mysql.connector
import pandas as pd
import plotly.express as px
import numpy as np
import importlib.util
import yfinance as yf

# ------------------------------- #
# CONFIG                          #
# ------------------------------- #
st.set_page_config(page_title="AI BI Assistant", layout="wide")

# ✨ Custom UI Styling
st.markdown("""
<style>
    .main { background-color: #f5f7fa; }
    .block-container { padding-top: 2rem; }
    div[data-testid="stMetric"] {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0px 2px 10px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ------------------------------- #
# DATABASE                        #
# ------------------------------- #
def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="your_password_here"  # Replace with your actual MySQL root password
    )

def setup_database():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS business_ai")
    cursor.execute("USE business_ai")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            chat_name VARCHAR(255),
            user_message TEXT,
            bot_reply TEXT,
            chat_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_chat(chat_name, user_msg, bot_msg):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("USE business_ai")
    cursor.execute(
        "INSERT INTO chat_history (chat_name, user_message, bot_reply) VALUES (%s, %s, %s)",
        (chat_name, user_msg, bot_msg)
    )
    conn.commit()
    conn.close()

def get_chats():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("USE business_ai")
    cursor.execute("""
        SELECT chat_name, MAX(chat_time) 
        FROM chat_history 
        GROUP BY chat_name 
        ORDER BY MAX(chat_time) DESC
    """)
    chats = [row[0] for row in cursor.fetchall()]
    conn.close()
    return chats

def load_chat(chat_name):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("USE business_ai")
    cursor.execute("""
        SELECT user_message, bot_reply 
        FROM chat_history 
        WHERE chat_name=%s 
        ORDER BY id
    """, (chat_name,))
    data = cursor.fetchall()
    conn.close()
    
    messages = []
    for u, b in data:
        messages.append({"role": "user", "content": u})
        messages.append({"role": "assistant", "content": b})
    return messages

def delete_chat(chat_name):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("USE business_ai")
    cursor.execute("DELETE FROM chat_history WHERE chat_name=%s", (chat_name,))
    conn.commit()
    conn.close()

def rename_chat(old_name, new_name):
    if not new_name or new_name.strip() == old_name:
        return False
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("USE business_ai")
    cursor.execute(
        "UPDATE chat_history SET chat_name=%s WHERE chat_name=%s",
        (new_name.strip(), old_name)
    )
    conn.commit()
    conn.close()
    return True

# ------------------------------- #
# AI FUNCTIONS                    #
# ------------------------------- #

def get_ticker(company):
    try:
        # Prompt explicitly forces a strict clean JSON key payload structure
        prompt = (
            f"Identify the official public stock market ticker symbol for '{company}'. "
            f"If the company is privately held, or its ticker cannot be found, set the ticker value to 'NONE'. "
            f"Return ONLY a valid JSON object matching this exact schema: "
            f'{{"ticker": "SYMBOL"}}'
        )
        res = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            response_format={"type": "json_object"}  # Forces strict native JSON formatting
        )
        
        # Parse clean structural JSON directly
        payload = json.loads(res.choices[0].message.content.strip())
        ticker = str(payload.get("ticker", "NONE")).strip().upper()
        ticker = ticker.replace('"', '').replace("'", "").replace("`", "")
        
        if "NONE" in ticker or len(ticker) > 6 or not ticker.isalnum():
            return None
            
        return ticker
    except Exception:
        return None




def is_company_related(prompt):
    res = client.chat.completions.create(
        messages=[
            {
                "role": "system", 
                "content": (
                    "You are a strict validation guard for a business intelligence app. "
                    "Determine if the user is inquiring about a company, corporate brand, enterprise, business entity, "
                    "or industrial market topic (e.g., OpenAI, Tesla, generic startups, tech giants, local firms). "
                    "Reply with exactly 'YES' if the prompt targets any company or commercial entity profile or their background. "
                    "Reply 'NO' ONLY if the question is completely non-corporate, a general knowledge topic unrelated to business, an unrelated math equation, a generic cooking recipe, or random chatter."
                )
            },
            {"role": "user", "content": prompt}
        ],
        model="llama-3.1-8b-instant"
    )
    decision = res.choices[0].message.content.strip().upper()
    return "YES" in decision

def get_response(prompt):
    res = client.chat.completions.create(
        messages=[
            {
                "role": "system", 
                "content": "You are a comprehensive Business Intelligence assistant. Provide crisp, thorough corporate data, structural profiles, background history, revenue details, and market rankings for the requested entity."
            },
            {"role": "user", "content": prompt}
        ],
        model="llama-3.1-8b-instant"
    )
    return res.choices[0].message.content

def detect_chart_type(prompt):
    res = client.chat.completions.create(
        messages=[{"role": "user", "content": f"Return chart type for: {prompt}. Choose from bar, line, scatter, pie, histogram"}],
        model="llama-3.1-8b-instant"
    )
    return res.choices[0].message.content.strip().lower()

def generate_insight(prompt):
    res = client.chat.completions.create(
        messages=[{"role": "user", "content": f"Give 3 business insights regarding corporate status or industrial positioning: {prompt}"}],
        model="llama-3.1-8b-instant"
    )
    return res.choices[0].message.content

def get_linkedin(company):
    try:
        # 🌟 IMPROVED PROMPT: Forces clean, short corporate brand handles over official legal entity suffixes.
        prompt = (
            f"Identify the primary, most common official LinkedIn company page URL for '{company}'. "
            f"Strictly avoid suffixes like '-se', '-inc', '-llc', '-corp', or country codes if a shorter vanity URL layout exists "
            f"(e.g., provide 'https://www.linkedin.com/company/sap' instead of 'sap-se', or 'https://linkedin.com' instead of 'google-inc'). "
            f"Output only the final clean absolute URL string. Do not provide markdown ticks, quotes, or conversational explanations."
        )
        res = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant"
        )
        url = res.choices[0].message.content.strip().replace('`', '').replace('"', '').replace("'", "")
        if "linkedin.com/company/" in url:
            return url
        return f"https://linkedin.com{company}"
    except:
        return f"https://linkedin.com{company}"
    
def generate_executive_summary(news_text):

    prompt = f"""
You are an executive briefing system.

News:
{news_text}

Create a concise briefing.

Output format:

Key Event:
(one sentence)

Business Impact:
(one sentence)

Future Outlook:
(one sentence)

Limit total response to 60 words.
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.choices[0].message.content

# ------------------------------- #
# INIT                            #
# ------------------------------- #
setup_database()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_name" not in st.session_state:
    st.session_state.chat_name = "Chat 1"


# Automatically find python files inside the utils folder
# ------------------------------- #
# SIDEBAR NAVIGATION (UTILS)       #
# ------------------------------- #
st.sidebar.title("🛠️ Utilities & Tools")

UTILS_DIR = "utils"
utils_modules = []

# Scan the folder for files
if os.path.exists(UTILS_DIR):
    utils_modules = [f for f in os.listdir(UTILS_DIR) if f.endswith(".py")]

# Clean up names for display
formatted_names = {f: f.replace(".py", "").replace("_", " ").title() for f in utils_modules}

# 🌟 CRITICAL OVERRIDE: Explicitly remove specific options from showing up
exclude_list = ["Grounding", "Competitor Battle"]
filtered_options = [name for name in formatted_names.values() if name not in exclude_list]


# Combine everything into the final navigation menu array
nav_options = [
    "🏠 Main Chat Assistant",
    "📊 Live Market Momentum",
    "💼 Executive Summary"
]

selected_page = st.sidebar.selectbox(
    "Go to page:",
    nav_options
)
st.sidebar.markdown("---")


# ------------------------------- #
# SIDEBAR CHATS                   #
# ------------------------------- #
if selected_page == "🏠 Main Chat Assistant":
    st.sidebar.title("💬 Chats")
    if st.sidebar.button("➕ New Chat"):
        st.session_state.messages = []
        st.session_state.chat_name = f"Chat {len(get_chats())+1}"
        st.rerun()

    for chat in get_chats():
        col1, col2 = st.sidebar.columns([3, 1])
        if col1.button(chat, key=f"btn_{chat}"):
            st.session_state.messages = load_chat(chat)
            st.session_state.chat_name = chat
            st.rerun()
        if col2.button("❌", key=f"del_{chat}"):
            delete_chat(chat)
            st.rerun()

    st.sidebar.markdown("---")
    new_name = st.sidebar.text_input("Rename Chat")
    if st.sidebar.button("Rename"):
        if rename_chat(st.session_state.chat_name, new_name):
            st.session_state.chat_name = new_name
            st.session_state.messages = load_chat(new_name)
            st.success("Renamed!")
            st.rerun()



# ------------------------------- #
# ROUTING PAGES CONTENT           #
# ------------------------------- #
if selected_page != "🏠 Main Chat Assistant":

    if selected_page == "📊 Live Market Momentum":
        st.title("📊 Live Market Momentum Tracker")
        st.markdown("This module calculates real-time technical indicators directly from historical exchange price arrays.")

        ticker_input = st.text_input("🏢 Enter Stock Ticker", value="TSLA", max_chars=5).strip().upper()

        if ticker_input:
            st.button("🔄 Recalculate Live Metrics")
            
            with st.spinner(f"Downloading raw data matrix for {ticker_input}..."):
                # yf.download is completely immune to the info dictionary blocking bug
                raw_candles = yf.download(ticker_input, period="1mo", interval="1d")
                
            if raw_candles is not None and not raw_candles.empty:
                # Unpack multi-index columns if present in newer yfinance versions
                if isinstance(raw_candles.columns, pd.MultiIndex):
                    raw_candles.columns = raw_candles.columns.get_level_values(0)
                
                # --- CALCULATE LIVE INDICATORS VIA PANDAS MATH ---
                close_prices = raw_candles["Close"]
                latest_price = float(close_prices.iloc[-1])
                previous_price = float(close_prices.iloc[-2])
                price_delta = latest_price - previous_price
                
                # 1. Moving Averages (5-day and 20-day SMA)
                sma_5 = float(close_prices.rolling(window=5).mean().iloc[-1])
                sma_20 = float(close_prices.rolling(window=20).mean().iloc[-1])
                
                # 2. Relative Strength Index (RSI - 14 Days)
                delta_series = close_prices.diff()
                gain = delta_series.clip(lower=0)
                loss = -delta_series.clip(upper=0)
                
                avg_gain = gain.rolling(window=14).mean().iloc[-1]
                avg_loss = loss.rolling(window=14).mean().iloc[-1]
                
                if avg_loss == 0:
                    rsi = 100.0
                else:
                    rs = avg_gain / avg_loss
                    rsi = 100.0 - (100.0 / (1.0 + rs))
                
                # --- RENDER STRIP METRIC CARDS ---
                st.markdown(f"### 📋 Real-Time Technical Snapshot: {ticker_input}")
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("💰 Latest Price", f"${latest_price:.2f}", delta=f"{price_delta:+.2f}")
                m2.metric("📈 5-Day Simple Moving Avg", f"${sma_5:.2f}")
                m3.metric("📉 20-Day Simple Moving Avg", f"${sma_20:.2f}")
                
                # Dynamic health flagging for RSI metrics
                if rsi >= 70:
                    rsi_status = "Overbought 🟥"
                elif rsi <= 30:
                    rsi_status = "Oversold 🟩"
                else:
                    rsi_status = "Neutral 🟨"
                m4.metric("⏱️ RSI (14D)", f"{rsi:.1f}", delta=rsi_status, delta_color="normal")
                
                # --- HISTORICAL TRACKING GRAPH ---
                st.markdown("### 📈 Monthly Closing Trajectory")
                df_chart = pd.DataFrame({
                    "Date": raw_candles.index,
                    "Closing Price ($)": close_prices.values
                })
                fig_mom = px.line(df_chart, x="Date", y="Closing Price ($)", title=f"{ticker_input} Price History Matrix", markers=True)
                fig_mom.update_layout(plot_bgcolor="white", paper_bgcolor="white")
                fig_mom.update_xaxes(showline=True, linewidth=1, linecolor='black', gridcolor='#f0f2f6')
                fig_mom.update_yaxes(showline=True, linewidth=1, linecolor='black', gridcolor='#f0f2f6')
                st.plotly_chart(fig_mom, use_container_width=True)
                
                st.success(f"✔ Core metrics computed directly from raw exchange transactions for {ticker_input}.")
            else:
                st.error(f"❌ Failed to download transaction history for ticker target: '{ticker_input}'. Check your connectivity or ticker name.")

    elif selected_page == "💼 Executive Summary":

        st.title("💼 Executive Summary Generator")

        st.markdown(
        "Generate executive-level business summaries from company news and reports."
        )

        news_text = st.text_area(
        "📰 Paste Company News",
        height=250
        )

        if st.button("🚀 Generate Executive Summary"):

            if news_text.strip():

             with st.spinner(
                "Generating executive briefing..."
            ):

                summary = generate_executive_summary(
                    news_text
                )

            st.markdown("---")

            st.markdown(
                "### 📋 Executive Briefing"
            )

            st.write(summary)

        else:

            st.warning(
                "Please enter company news first."
            )   
    else:
        # Fallback to loading standard physical files from utils folder
        matching_files = [k for k, v in formatted_names.items() if v == selected_page]
        
        if matching_files:
            filename = matching_files[0]
            file_path = os.path.join(UTILS_DIR, filename)
            
            st.title(f"🛠️ {selected_page}")
            
            try:
                spec = importlib.util.spec_from_file_location(filename.replace(".py", ""), file_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                if hasattr(module, "main"):
                    module.main()
            except Exception as e:
                st.error(f"Error rendering utility file '{filename}': {e}")
        else:
            pass

    


    
    # 🌟 Handle your newly added manual option pages first
    if selected_page == "📈 Market Trends Lookup":
        st.title("📈 Market Trends Lookup")
        st.info("Market analysis workspace module active.")
        # Place your custom code or text input boxes for trends here
        
    elif selected_page == "🏢 Executive Database":
        st.title("🏢 Executive Database")
        st.info("Corporate leadership indexing tracker module active.")
        # Place your custom database queries here
        
        # 🌟 GATE 4: Fallback Loop for remaining physical files inside the utils directory
        
    else:
        # Prevent manual customized UI page choices from ever entering the disk scanning loop
        manual_ui_pages = ["📊 Live Market Momentum"]
        
        if selected_page in manual_ui_pages:
            pass  # Safely exits without running any background file scans
        else:
            matching_files = [k for k, v in formatted_names.items() if v == selected_page]
            if matching_files:
                filename = matching_files[0]
                file_path = os.path.join(UTILS_DIR, filename)
                st.title(f"🛠️ {selected_page}")
                try:
                    spec = importlib.util.spec_from_file_location(filename.replace(".py", ""), file_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    if hasattr(module, "main"):
                        module.main()
                except Exception as e:
                    pass  # Suppresses unexpected sub-module import crashes


else:
    # ------------------------------- #
    # DEFAULT MAIN UI (CHAT ASSISTANT)#
    # ------------------------------- #
    st.title("🤖 AI Business Intelligence Assistant")
    st.markdown(f"📌 Current Chat: {st.session_state.chat_name}")
    
    # Chat display
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    # ------------------------------- #
    # INPUT                           #
    # ------------------------------- #
    if prompt := st.chat_input("Ask about companies, charts, insights..."):
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        prompt_lower = prompt.lower()
        
        # Grounding Validation Check
        if not is_company_related(prompt):
            reply = "⚠️ I am restricted to providing corporate information and company-related details only. Please adjust your query to target a specific business entity."
            st.chat_message("assistant").warning(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
            save_chat(st.session_state.chat_name, prompt, reply)
        else:
            # LINKEDIN INTERCEPTION
            if "linkedin" in prompt_lower:
                clean_name = prompt_lower.replace("linkedin", "").replace("of", "").replace("profile", "").replace("url", "").strip()
                reply = f"🔗 {get_linkedin(clean_name)}"
                st.chat_message("assistant").markdown(reply)
            # CHART GENERATION
            elif "chart" in prompt_lower:
                years = list(range(2020, 2027))
                df = pd.DataFrame({"Year": years, "Value": np.random.randint(80, 150, 7)})
                chart_type = detect_chart_type(prompt)
                if "line" in chart_type:
                    fig = px.line(df, x="Year", y="Value")
                elif "scatter" in chart_type:
                    fig = px.scatter(df, x="Year", y="Value")
                elif "pie" in chart_type:
                    fig = px.pie(df, values="Value", names="Year")
                else:
                    fig = px.bar(df, x="Year", y="Value")
                st.plotly_chart(fig, use_container_width=True)
                insight = generate_insight(prompt)
                st.markdown("### 💡 Insights")
                st.write(insight)
                reply = "Chart + insights generated"
            else:
                # 🌟 LIVE REVENUE INTERCEPTOR LAYER
                financial_keywords = ["revenue", "sales", "financials", "turnover", "earn", "profit", "worth", "figures", "reported"]
                if any(kw in prompt_lower for kw in financial_keywords):
                    with st.spinner("Retrieving live market metrics for context grounding..."):
                        try:
                            # Strict system layout instruction forcing the model to output a single clean uppercase target word
                            extraction_prompt = (
                                f"Identify the primary target company or business entity being discussed in this text: '{prompt}'. "
                                f"Output ONLY the raw common name of that company (e.g., 'SAP', 'Apple', 'Tesla'). "
                                f"Do not write legal suffixes, punctuation, paragraphs, or any explanations."
                            )
                            extract_res = client.chat.completions.create(
                                messages=[{"role": "user", "content": extraction_prompt}],
                                model="llama-3.1-8b-instant"
                            )
                            
                            # Clean up the output using Regex to strip out unexpected trailing punctuation or code symbols
                            raw_extracted_name = extract_res.choices[0].message.content.strip()
                            clean_company_name = re.sub(r'[^a-zA-Z0-9\s]', '', raw_extracted_name).split('\n')[0].strip()
                            
                            # Resolve ticker from the isolated, clean company string handle
                            ticker = get_ticker(clean_company_name)
                        except Exception:
                            ticker = get_ticker(prompt)
                            
                        live_context = ""
                        
                        if ticker:
                            try:
                                ticker_ob = yf.Ticker(ticker)
                                info = ticker_ob.info
                                raw_rev = info.get("totalRevenue") or info.get("grossProfits") or info.get("revenue")
                                
                                if raw_rev:
                                    live_context = (
                                        f"\n[CRITICAL REAL-TIME GROUNDING CONTEXT FOR CURRENT YEAR 2026]: "
                                        f"The user is viewing or discussing outdated corporate metrics. "
                                        f"You MUST forcefully override any old 2022/2023 financial statistics with these new live figures. "
                                        f"Live exchange data fetched right now for ticker target '{ticker}': "
                                        f"The most recent Trailing Twelve Months (TTM) Total Revenue is ${float(raw_rev)/1_000_000_000:.2f} Billion USD. "
                                        f"The current total global workforce headcount is {info.get('fullTimeEmployees', 'N/A')} employees. "
                                        f"State clearly that according to real-time 2026 financial market registries, the company's revenue is updated to this new figure. "
                                        f"Do not mention that you received context via an injection wrapper."
                                    )
                            except Exception:
                                pass
                    
                    # Call client dynamically with injected context grounding parameters
                    res = client.chat.completions.create(
                        messages=[
                            {"role": "system", "content": "You are a professional Business Intelligence assistant. You are grounded with live 2026 market data. Your priority is to correct any outdated historical assumptions or text in the chat history using the provided live context data layer parameters."},
                            {"role": "user", "content": prompt + live_context}
                        ],
                        model="llama-3.1-8b-instant"
                    )
                    reply = res.choices[0].message.content
                    st.chat_message("assistant").markdown(reply)
                else:
                    # Default conversation pipeline path if no revenue keywords are found
                    reply = get_response(prompt)
                    st.chat_message("assistant").markdown(reply)


            
            st.session_state.messages.append({"role": "assistant", "content": reply})
            save_chat(st.session_state.chat_name, prompt, reply)

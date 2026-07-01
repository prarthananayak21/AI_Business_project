import mysql.connector

def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="sql@21",  # change this
        database="business_ai"
    )

# Create table automatically
def create_table():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS search_history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            query TEXT,
            search_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

# Save search automatically
def save_search(query):
    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO search_history (query) VALUES (%s)",
            (query,)
        )

        conn.commit()
        conn.close()

    except Exception as e:
        print("DB Error:", e)

# Get last 10 searches
def get_history():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT query FROM search_history
        ORDER BY search_time DESC
        LIMIT 10
    """)

    data = cursor.fetchall()
    conn.close()

    return [d[0] for d in data]
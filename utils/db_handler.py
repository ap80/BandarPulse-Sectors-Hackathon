import os
import sqlite3
import pandas as pd
from datetime import datetime

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "cache.db")

def get_connection(db_path=None):
    """Establishes a connection to the SQLite cache database."""
    if db_path is None:
        db_path = os.getenv("DATABASE_PATH", DEFAULT_DB_PATH)
    
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path=None):
    """Initializes tables for BandarPulse local persistent caching."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    # 1. Companies Table (Stores fundamental, valuation, and listing data)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS companies (
        symbol TEXT PRIMARY KEY,
        company_name TEXT,
        sector TEXT,
        sub_sector TEXT,
        listing_board TEXT,
        market_cap REAL,
        pe_ttm REAL,
        pbv_mrq REAL,
        roe_ttm REAL,
        der_mrq REAL,
        close_price REAL,
        volume REAL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 2. Broker Summary / Flow Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS broker_flow (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT,
        trade_date DATE,
        broker_code TEXT,
        buyer_seller_type TEXT,
        net_volume REAL,
        net_value REAL,
        avg_price REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 3. Ingestion Logs & Quota Tracker
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ingestion_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        endpoint TEXT,
        credits_used INTEGER DEFAULT 1,
        status TEXT,
        records_fetched INTEGER,
        log_message TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    conn.commit()
    conn.close()
    print(f"[INFO] SQLite database initialized successfully at: {db_path or DEFAULT_DB_PATH}")

def save_companies(df: pd.DataFrame, db_path=None):
    """Saves or updates companies dataframe in SQLite cache."""
    if df is None or df.empty:
        print("[WARNING] Empty DataFrame provided, skipping save.")
        return 0
    
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    # Standardize column names if needed
    cols = df.columns.tolist()
    
    # Use REPLACE INTO for idempotence
    records_saved = 0
    for _, row in df.iterrows():
        symbol = row.get("symbol") or row.get("ticker")
        if not symbol:
            continue
            
        cursor.execute("""
        INSERT OR REPLACE INTO companies (
            symbol, company_name, sector, sub_sector, listing_board,
            market_cap, pe_ttm, pbv_mrq, roe_ttm, der_mrq,
            close_price, volume, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(symbol).upper(),
            row.get("company_name", ""),
            row.get("sector", ""),
            row.get("sub_sector", ""),
            row.get("listing_board", "MAIN"),
            row.get("market_cap", 0.0),
            row.get("pe_ttm", None),
            row.get("pbv_mrq", None),
            row.get("roe_ttm", None),
            row.get("der_mrq", None),
            row.get("close_price", row.get("close", 0.0)),
            row.get("volume", 0.0),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        records_saved += 1
        
    conn.commit()
    conn.close()
    print(f"[INFO] Saved {records_saved} company records to SQLite cache.")
    return records_saved

def load_companies(sector_filter=None, min_market_cap=None, db_path=None) -> pd.DataFrame:
    """Loads companies from SQLite cache with optional filters."""
    conn = get_connection(db_path)
    query = "SELECT * FROM companies WHERE 1=1"
    params = []
    
    if sector_filter and sector_filter != "All":
        query += " AND sector = ?"
        params.append(sector_filter)
        
    if min_market_cap and min_market_cap > 0:
        query += " AND market_cap >= ?"
        params.append(min_market_cap)
        
    query += " ORDER BY market_cap DESC"
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def log_ingestion(endpoint: str, credits_used: int, status: str, records_fetched: int, message: str = "", db_path=None):
    """Records an API request log to monitor quota usage."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO ingestion_logs (endpoint, credits_used, status, records_fetched, log_message)
    VALUES (?, ?, ?, ?, ?)
    """, (endpoint, credits_used, status, records_fetched, message))
    conn.commit()
    conn.close()

def get_ingestion_summary(db_path=None):
    """Returns total credits used and recent ingestion activities."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COALESCE(SUM(credits_used), 0) AS total_credits FROM ingestion_logs")
    total_credits = cursor.fetchone()["total_credits"]
    
    cursor.execute("SELECT COUNT(*) AS total_companies FROM companies")
    total_companies = cursor.fetchone()["total_companies"]
    
    cursor.execute("SELECT * FROM ingestion_logs ORDER BY timestamp DESC LIMIT 5")
    recent_logs = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return {
        "total_credits_used": total_credits,
        "total_companies_cached": total_companies,
        "recent_logs": recent_logs
    }

if __name__ == "__main__":
    init_db()
    summary = get_ingestion_summary()
    print("Ingestion Summary:", summary)

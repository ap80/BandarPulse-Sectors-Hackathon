import os
import sys
import requests
import pandas as pd
from dotenv import load_dotenv

# Add parent directory to sys.path to ensure utils module can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.db_handler import init_db, save_companies, log_ingestion

load_dotenv()

API_KEY = os.getenv("SECTORS_API_KEY")
BASE_URL = "https://api.sectors.app/v2"
USE_MOCK = os.getenv("USE_MOCK", "False").lower() in ("true", "1", "t")

def get_headers():
    return {
        "Authorization": API_KEY
    }

def fetch_companies_data(structured_where=None, order_by=None, save_to_cache=True):
    """
    Fetches company listing and financial metrics from Sectors API v2.
    Uses structured query params ('where', 'order_by') which consume only 1 credit
    instead of 3 credits consumed by natural language query (?q=).
    """
    if USE_MOCK:
        print("[MOCK MODE] Menggunakan mock data lokal (0 kredit terpakai).")
        mock_data = [
            {
                "symbol": "BBCA", "company_name": "Bank Central Asia Tbk", "sector": "Financials",
                "sub_sector": "Banks", "listing_board": "MAIN", "market_cap": 1250000000000000,
                "pe_ttm": 21.4, "pbv_mrq": 4.5, "roe_ttm": 21.8, "der_mrq": 4.8, "close_price": 10250, "volume": 68000000
            },
            {
                "symbol": "PTBA", "company_name": "Bukit Asam Tbk", "sector": "Energy",
                "sub_sector": "Coal", "listing_board": "MAIN", "market_cap": 31000000000000,
                "pe_ttm": 6.8, "pbv_mrq": 1.6, "roe_ttm": 24.2, "der_mrq": 0.5, "close_price": 2710, "volume": 42000000
            },
            {
                "symbol": "ACES", "company_name": "Aspirasi Hidup Indonesia Tbk", "sector": "Consumer Cyclicals",
                "sub_sector": "Retail", "listing_board": "MAIN", "market_cap": 14500000000000,
                "pe_ttm": 17.5, "pbv_mrq": 2.3, "roe_ttm": 13.9, "der_mrq": 0.2, "close_price": 845, "volume": 35000000
            },
            {
                "symbol": "MEDC", "company_name": "Medco Energi Internasional Tbk", "sector": "Energy",
                "sub_sector": "Oil & Gas", "listing_board": "MAIN", "market_cap": 34000000000000,
                "pe_ttm": 7.2, "pbv_mrq": 1.1, "roe_ttm": 16.4, "der_mrq": 1.9, "close_price": 1350, "volume": 58000000
            },
            {
                "symbol": "BRMS", "company_name": "Bumi Resources Minerals Tbk", "sector": "Basic Materials",
                "sub_sector": "Metals & Mining", "listing_board": "MAIN", "market_cap": 24000000000000,
                "pe_ttm": 35.0, "pbv_mrq": 1.8, "roe_ttm": 5.2, "der_mrq": 0.3, "close_price": 172, "volume": 125000000
            }
        ]
        df = pd.DataFrame(mock_data)
        if save_to_cache:
            init_db()
            save_companies(df)
            log_ingestion("mock_companies", 0, "SUCCESS", len(df), "Mock data loaded into SQLite cache")
        return df

    if not API_KEY:
        print("[ERROR] SECTORS_API_KEY tidak ditemukan di environment (.env).")
        return None

    url = f"{BASE_URL}/companies/"
    params = {}
    if structured_where:
        params["where"] = structured_where
    if order_by:
        params["order_by"] = order_by

    headers = get_headers()
    try:
        print(f"[INFO] Memanggil Sectors API: {url} | Params: {params}")
        response = requests.get(url, headers=headers, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Handle cases where response might be wrapped in a dict or list
        if isinstance(data, dict):
            records = data.get("results", data.get("data", data.get("companies", [data])))
        elif isinstance(data, list):
            records = data
        else:
            records = []
            
        print(f"[INFO] Berhasil menarik {len(records)} data emiten dari Sectors API.")
        df = pd.DataFrame(records)
        
        if save_to_cache and not df.empty:
            init_db()
            save_companies(df)
            log_ingestion("/v2/companies/", 1, "SUCCESS", len(df), f"Fetched {len(df)} records via structured query")
            
        return df

    except requests.exceptions.HTTPError as err:
        print(f"[ERROR] HTTP Error saat request ke Sectors API: {err}")
        log_ingestion("/v2/companies/", 0, "FAILED", 0, str(err))
        return None
    except Exception as err:
        print(f"[ERROR] Request gagal: {err}")
        log_ingestion("/v2/companies/", 0, "ERROR", 0, str(err))
        return None

def fetch_company_report(symbol: str, save_to_cache=True):
    """
    Fetches detailed fundamental and valuation report for a specific ticker.
    Endpoint: /v2/company/report/{ticker}/
    """
    if not API_KEY:
        print("[ERROR] SECTORS_API_KEY tidak ditemukan.")
        return None
        
    # Clean ticker (e.g. BBCA.JK or BBCA)
    clean_symbol = symbol.replace(".JK", "").strip().upper()
    url = f"{BASE_URL}/company/report/{clean_symbol}/"
    headers = get_headers()
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        overview = data.get("overview", {})
        valuation = data.get("valuation", {})
        financials = data.get("financials", {})
        
        # Extract ratios from latest available historical financial ratio
        ratios = financials.get("historical_financial_ratio", [])
        latest_ratio = ratios[-1] if isinstance(ratios, list) and ratios else {}
        leverage = latest_ratio.get("leverage", {})
        profitability = latest_ratio.get("profitability", {})

        report_row = {
            "symbol": f"{clean_symbol}.JK",
            "company_name": data.get("company_name", ""),
            "sector": overview.get("sector", ""),
            "sub_sector": overview.get("sub_sector", overview.get("industry", "")),
            "listing_board": overview.get("listing_board", "MAIN"),
            "market_cap": overview.get("market_cap", valuation.get("market_cap", 0.0)),
            "pe_ttm": valuation.get("forward_pe", valuation.get("pe_ratio")),
            "pbv_mrq": valuation.get("pb_ratio"),
            "roe_ttm": profitability.get("roe"),
            "der_mrq": leverage.get("debt_to_equity_ratio"),
            "close_price": valuation.get("last_close_price", overview.get("last_close_price", 0.0)),
            "volume": valuation.get("volume", 0.0)
        }
        
        df = pd.DataFrame([report_row])
        if save_to_cache:
            init_db()
            save_companies(df)
            log_ingestion(f"/v2/company/report/{clean_symbol}/", 1, "SUCCESS", 1, f"Report cached for {clean_symbol}")
            
        return report_row
    except Exception as err:
        print(f"[ERROR] Gagal mengambil report {clean_symbol}: {err}")
        log_ingestion(f"/v2/company/report/{clean_symbol}/", 0, "FAILED", 0, str(err))
        return None

if __name__ == "__main__":
    init_db()
    # Test fetch (hanya mengonsumsi 1 kredit berkat structured query)
    df = fetch_companies_data()
    if df is not None:
        print("\n--- Cuplikan Data Emiten ---")
        print(df.head())

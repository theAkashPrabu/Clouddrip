"""
test_connection.py
Checks that Python can talk to our Azure SQL database (clouddrip-db).
If this works, the loader script in step 5.4 will work too.
"""

import os
import urllib.parse

from dotenv import load_dotenv
from sqlalchemy import create_engine, text


def get_engine():
    """Build a SQLAlchemy 'engine' = a reusable connection to Azure SQL."""
    load_dotenv()  # read the secrets from .env (never hard-code passwords)

    # The ODBC connection string: which driver, which server, who we are
    odbc = (
        "Driver={ODBC Driver 18 for SQL Server};"
        f"Server=tcp:{os.getenv('SQL_SERVER')},1433;"
        f"Database={os.getenv('SQL_DATABASE')};"
        f"Uid={os.getenv('SQL_USER')};"
        f"Pwd={os.getenv('SQL_PASSWORD')};"
        "Encrypt=yes;"                 # Azure requires encrypted connections
        "TrustServerCertificate=no;"   # check Azure's real certificate
        "Connection Timeout=90;"       # give the serverless DB time to wake up
    )
    # quote_plus makes special characters (like @ in passwords) URL-safe
    url = "mssql+pyodbc:///?odbc_connect=" + urllib.parse.quote_plus(odbc)

    # fast_executemany = send rows in big batches (much faster loading later)
    return create_engine(url, fast_executemany=True)


if __name__ == "__main__":
    engine = get_engine()
    with engine.connect() as conn:
        row = conn.execute(text("SELECT DB_NAME() AS db, SYSUTCDATETIME() AS utc_now")).one()
        print(f"✅ Connected to: {row.db}")
        print(f"🕒 Server time (UTC): {row.utc_now}")
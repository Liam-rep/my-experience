import pandas as pd
from persistance.tables.connection.bd_conn import get_conn

def get_all_prefer():
    try:
        conn= get_conn()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM integration")
            row = cursor.fetchall()
            df_pref = pd.DataFrame(row, columns=["user_id", "book_id", "rating"])
            return df_pref
    except Exception as error:
        return {"error": str(error)}
    finally:
        if conn:
            conn.close()
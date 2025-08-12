import pandas as pd
from persistance.tables.connection.bd_conn import get_conn

def query_integration(user_id):    
    try:
        """Загружаем данные из таблцы interactions"""
        conn = get_conn()
        with conn.cursor() as cursor:
            cursor.execute("SELECT i.user_id, i.book_id, i.rating, b.authors, b.categories FROM integration i JOIN books b ON i.book_id = b.book_id WHERE i.user_id =%s", (user_id,))
            row = cursor.fetchall()
            df = pd.DataFrame(row, columns=["user_id", "book_id", "rating", "authors", "categories"])
        print("я вытащил данные из таблицы integration")
        return df        
    except Exception as error:
        print(f"Что-то пошло не так: {error}")
        return pd.DataFrame()
    finally:
        conn.close()
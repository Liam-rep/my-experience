import pandas as pd
from persistance.tables.connection.bd_conn import get_conn

def get_user_preferences(user_id):
    """Определяет предпочтения пользователя на основе его оценок"""
    print("we are in get_user_preferences")
    conn = get_conn()
    with conn.cursor() as cursor:
    # Получаем книги, которые пользователь оценил выше 3
        cursor.execute("SELECT i.book_id, b.categories, b.authors FROM integration i JOIN books b ON i.book_id = b.book_id WHERE i.user_id = %s AND i.rating >= 3.0", (int(user_id),))
        row = cursor.fetchall()
        df = pd.DataFrame(row, columns=["book_id", "categories", "authors"])
    print("Я сделаль запрос)")
    conn.close()
    print(f"df:{df}")
    if df.empty:
        return {"categories": [], "authors": []}  # Если нет данных, возвращаем пустой список
    
    # Считаем частоту жанров и авторов
    cat_counts = df["categories"].value_counts()
    author_counts = df["authors"].value_counts()
    
    top_cat = cat_counts.head(5).index.tolist()
    top_authors = author_counts.head(5).index.tolist()
    
    return {"categories": top_cat, "authors": top_authors}

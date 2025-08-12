import pandas as pd
from implicit.nearest_neighbours import TFIDFRecommender 
from rectools.dataset import Dataset
from rectools.models import ImplicitItemKNNWrapperModel

from persistance.tables.connection.bd_conn import get_conn
from application.content_based import get_user_preferences
from application.query_integration import query_integration
from application.request_get.users import col_users
from application.save_rec import save_rec_todb
from application.get_all_prefer import get_all_prefer


from persistance.tables.connection.bd_conn import get_conn

def get_preferences(user_id):
    conn = get_conn()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT user_id, book_id, rating FROM integration WHERE user_id = %s", (user_id,))
            row = cursor.fetchall()
            print(f"row: {row}")
            result = pd.DataFrame(row, columns=["user_id", "book_id", "score"])
            return result
    except Exception as error:
        return {"status":"error", "message":str(error)}
    finally:
        conn.close()


def content_model(user_id):
    """Модель с использованием жанров и автроров"""
    conn = get_conn()
    preferences = get_user_preferences(user_id)
    print("preferences done")
    if not preferences["categories"] and not preferences["authors"]:
        return pd.DataFrame(columns=["user_id", "book_id", "score"])
    with conn.cursor() as cursor:
        query = """SELECT book_id, categories, authors FROM books WHERE categories IN %s OR authors IN %s"""
        cursor.execute(query, (tuple(preferences["categories"]), tuple(preferences["authors"])))
        row = cursor.fetchall()
        df = pd.DataFrame(row, columns=["book_id", "categories", "authors"])
    conn.close()
    df["score"] = df["categories"].apply(lambda x: sum(c in preferences["categories"] for c in x.split(','))) + \
              df["authors"].apply(lambda x: sum(a in preferences["authors"] for a in x.split(',')))
    return df[["book_id", "score"]].assign(user_id=user_id)

def knn_model(user_id):
    """KNN модель"""
    df_knn = get_all_prefer()
    if df_knn.empty:
        print("NO DATA")
        return
    rec_cont = pd.concat([content_model(user_id) for user_id in df_knn["user_id"].unique()])
    rec_cont = rec_cont.rename(columns={"book_id": "item_id"}) 
    df_knn = df_knn.rename(columns={"book_id": "item_id", "rating": "weight"})
    df_knn["score"]=0
    if not rec_cont.empty:
        df_knn["weight"] += df_knn["score"] * 2  # Увеличиваем вклад контентных предпочтений
    else:
        df_knn["score"] = 0  # Без контентной модели
        
    print(f"df_knn= {df_knn}")
    df_knn["datetime"] = pd.Timestamp.now()
    
    dataset = Dataset.construct(df_knn)

    model = ImplicitItemKNNWrapperModel(TFIDFRecommender())
    model.fit(dataset)
    rec_knn = model.recommend(users = df_knn["user_id"].tolist(), dataset=dataset, k=20, filter_viewed=False)
    rec_knn = rec_knn.merge(df_knn[["item_id", "weight"]], on="item_id", how="outer")
    rec_knn["weight"] = rec_knn["weight"].fillna(0) 

    if not rec_knn.empty:
        missing_books = rec_cont[~rec_cont["item_id"].isin(rec_knn["item_id"])]
        rec_knn = pd.concat([rec_knn, missing_books], ignore_index=True)
    else:
        rec_knn = rec_cont.copy()  # Если KNN не дал рекомендации, используем content-based
    
    preferences = get_preferences(user_id)
    col = col_users()
    print(f"col= {col}")
    print(f"rec_knn= {rec_knn}")
    
    if col < 5:
        rec_knn["final_score"] = rec_knn["score"]  # Только контентная модель
    else:
        rec_knn["final_score"] = ((rec_knn["weight"] + rec_knn["score"]) / 2).fillna(0)
    print(f"rec_knn = {rec_knn}")
    print(f"preferences = {preferences}")
    filtered_rec_knn = rec_knn[~rec_knn["item_id"].isin(preferences["book_id"])] # ~ - инвертор 
    final_rec = filtered_rec_knn[["user_id", "item_id", "final_score"]]
    final_rec = final_rec.dropna()


    print(f"final_rec = {final_rec}")
    recommended_books = []
    for _, row in final_rec.iterrows():
        rec_book = {
            "item_id": row["item_id"],
            "final_score": row["final_score"],
            "categories": rec_cont.get("categories", {}).get(row["item_id"], ""),
            "authors": rec_cont.get("authors", {}).get(row["item_id"], "")
        }
        recommended_books.append(rec_book)

    # Вычисляем Precision@10 на основе жанров, авторов и KNN
    precision_score = precision_at_k(recommended_books, get_user_preferences(user_id), k=10)

    print(f"Precision@10 для пользователя {user_id}: {precision_score:.4f}")

    save_rec_todb(final_rec)


def precision_at_k(recommended_books, user_preferences, k=10):
    """Вычисляет Precision@K на основе жанров, авторов и KNN-score"""
    top_k = recommended_books[:k]  # Берём первые K книг
    relevant_hits = sum(1 for book in top_k if is_relevant(book, user_preferences))
    return relevant_hits / k if k > 0 else 0

def is_relevant(book, user_preferences):
    """Определяет релевантность книги на основе жанров, авторов и KNN-score"""
    book_genres = set(book["categories"].split(',')) if isinstance(book["categories"], str) else set()
    book_authors = set(book["authors"].split(',')) if isinstance(book["authors"], str) else set()

    preferred_genres = set(user_preferences.get("categories", []))
    preferred_authors = set(user_preferences.get("authors", []))

    genre_match = bool(book_genres & preferred_genres)  # Есть совпадение жанров?
    author_match = bool(book_authors & preferred_authors)  # Совпадают авторы?
    knn_score = book.get("final_score", 0)  # Итоговый скор KNN

    return genre_match or author_match or knn_score > 0.5






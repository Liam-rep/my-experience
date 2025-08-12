import json
from persistance.tables.connection.bd_conn import get_conn

def save_rec_todb(final_rec):
    """Сохраняем рекомендации в PostgreSQL в формате JSONB"""
    conn = get_conn()
    try:
        with conn.cursor() as cursor:
            for user_id in final_rec["user_id"].unique():
                user_recs = final_rec[final_rec["user_id"] == user_id][["item_id", "final_score"]].to_dict(orient="records")
                json_data = json.dumps(user_recs)
                cursor.execute("INSERT INTO rec (user_id, recomm) VALUES (%s, %s) ON CONFLICT (user_id) DO UPDATE SET recomm = %s", (int(user_id), json_data, json_data))
            conn.commit()
        print("Рекомендации пришли в БД (JSONB)")
    except Exception as error:
        print(f"Ошибка при сохранении рекомендаций: {error}")       
    finally:
        conn.close()


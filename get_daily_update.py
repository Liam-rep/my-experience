from persistance.tables.connection.bd_conn import get_conn
from application.recsyst import knn_model

def get_active_users():
    """Получаем пользователей, которые были активны за последние 24 часа"""
    conn = get_conn()
    with conn.cursor() as cursor:
        cursor.execute("SELECT user_id FROM users WHERE last_login >= NOW() - INTERVAL '1 day'")
        users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users
def daily_update():
    users = get_active_users()
    for user_id in users:
        knn_model(user_id)  # Пересчет рекомендаций
    print(f"Обновлены рекомендации для {len(users)} пользователей")

def last_login(user_id):
    try:
        conn = get_conn()
        with conn.cursor() as cursor:
            cursor.execute("UPDATE users SET last_login = NOW() WHERE id = %s", (user_id))
            return {"status":"success"}
    except Exception as error:
        return {"status":"error", "msg":str(error)}
    finally:
        if conn:
            conn.close()
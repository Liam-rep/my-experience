from persistance.tables.connection.bd_conn import get_conn

def get_user_id(email):
    conn = get_conn()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT user_id FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            if not user:
                return {"status":"error", "message": "Пользователь не найден"}
            else:
                return {"status":"success", "user_id":user[0]}
    except Exception as error:
        return {"status":"error", "message":str(error)}
    finally:
        conn.close()
from flask import Flask, request, jsonify
from flask import request, make_response
from flask_jwt_extended import JWTManager, unset_jwt_cookies, create_access_token,create_refresh_token,set_refresh_cookies, set_access_cookies, jwt_required, get_jwt_identity
import os
from flask_cors import CORS
from application.user_id import get_user_id
from application.recsyst import knn_model
from application.request_get.books import get_all_books
from application.request_get.book_id import get_book_id
from application.request_post.add_user import signup
from application.request_post.compare_user import auth
from application.request_post.searchbook import search
from application.request_post.user_rating import user_rating
from application.request_get.get_users_rating import get_users_rating
from application.request_get.get_rec import get_rec
from application.request_post.rec_book import rec_books
from application.request_get.get_library import get_library
from application.request_post.filter import filtering
from application.request_post.comm import set_comm
from application.request_get.get_comm import get_comments
from application.request_get.get_posts import get_posts
from application.request_get.get_post_id import get_post_id
from application.request_post.add_post import add_post
from application.request_update.update_post import update_post
from application.request_delete.delete_post import del_post
from application.request_update.update_comm import update_comm
from application.request_delete.delete_comm import del_comm
from application.request_get.get_comments_post import get_comments_post
from application.request_post.set_comm_post import set_comm_post
from application.request_post.add_catalog import add_catalog
from application.request_get.get_cat import get_cat
from application.request_get.get_cat_id import get_cat_id
from application.request_post.add_cat_book import add_cat_book
from application.request_get.get_catalog import get_catalog
from application.request_delete.del_book_cat import del_book_cat
from application.request_delete.del_cat import del_cat
from application.get_daily_update import last_login
import schedule
import time
import threading
from application.get_daily_update import daily_update

liberoom = Flask(__name__)
liberoom.config['SECRET_KEY'] = 'aiTTt7zORZCbIbmX'

liberoom.config['JWT_TOKEN_LOCATION'] = ['cookies']
liberoom.config['JWT_ACCESS_COOKIE_NAME'] = 'access_token'
liberoom.config['JWT_REFRESH_COOKIE_NAME'] = 'refresh_token'
liberoom.config['JWT_COOKIE_CSRF_PROTECT'] = False  # для разработки
liberoom.config["JWT_COOKIE_SECURE"] = False
liberoom.config['JWT_ACCESS_COOKIE_PATH'] = '/'
liberoom.config['JWT_REFRESH_COOKIE_PATH'] = '/refresh'


jwt = JWTManager(liberoom)
CORS(liberoom, supports_credentials=True, origins=["http://127.0.0.1:5173"])

schedule.every().day.at("03:00").do(daily_update) #обновление рекомендаций

def run_shedule():
    while True:
        schedule.run_pending()
        time.sleep(60) 

sh_thread = threading.Thread(target=run_shedule, daemon=True)
sh_thread.start()

@liberoom.route('/books', methods=['GET'])
def get_books():
    books = get_all_books()
    return jsonify(books)

@liberoom.route('/reg', methods=['POST']) #регистрация ЁУ
def reg():
    try:
        data = request.json
        name = data.get("username")
        email = data.get("useremail")
        hashpass = data.get("userhashpass")        
        print("data пришла")

        result = signup(name, email, hashpass)
        if result["status"] == "success": 
            return jsonify({"message":"Юху! Новый пользователь!!"}), 200                
        else:
            return jsonify({"message": result["message"]}), 500
    except Exception as error:
        print(f"we gotta problem here: {error}")
        return jsonify({"message": "Произошла ошибка на сервере"}), 500
    

@liberoom.route('/signin', methods=['POST'])
def signin():
    try:
        data = request.json
        email = data.get("useremail")
        hashpass = data.get("userhashpass")        
        print("data пришла")

        result = auth(email, hashpass)
        if result["status"] == "success":
            access_token = create_access_token(identity=email)
            refresh_token = create_refresh_token(identity=email)

            response = jsonify({"login": "ok"})
            set_access_cookies(response, access_token)
            set_refresh_cookies(response, refresh_token)
            user_id = get_user_id(email)
            if user_id["status"] == "success":
                print("user_id there")
                last_login(user_id)
                knn_model(user_id["user_id"]) #рекомендашка
            return response
        else:
            return jsonify({"message": result["message"]}), 401     
    except Exception as error:
        print(f"Ошибка при проверке: {error}")
        return jsonify({"message": "Ошибка при проверке"}), 500
      
@liberoom.route('/leave', methods=['GET'])
@jwt_required()
def sign_out():
    try:
        current_user=get_jwt_identity()
        response = jsonify({"login": "ok", "clear_local_storage": True})
        unset_jwt_cookies(response)
        return response
    except Exception as error:
        print(f"Ошибка при : {error}")
        return jsonify({"message": "Ошибка при проверке"}), 500
    
@liberoom.route('/profile', methods=['GET', 'POST'])
@jwt_required()
def profile():
    current_user = get_jwt_identity()
    if request.method == 'GET':
        return jsonify({"message": f"Добро пожаловать, {current_user}!"}), 200
    elif request.method == 'POST':
        try:
            data = request.json
            words = data.get("searchData")
            result = search(words)
            if result["status"] == "success":
                return jsonify(result), 200
            else:
                print("Ошибка: результат поиска не был найден.")
                return jsonify(result["message"]), 500
        except Exception as error:
            print(f"Ошибка при поиске: {error}")
            return jsonify({"message": "Ошибка при поиске"}), 500

@liberoom.route('/move', methods=['POST'])
@jwt_required()
def move():
    current_user = get_jwt_identity()
    print(f"user safe {current_user}")
    try:
        data = request.json
        book_id = data.get("book_id")
        print(f"data book_id {book_id} was recieved")

        result = get_book_id(book_id)
        if result["status"] == "success":
            return jsonify(result), 200
        else:
            print(f"Ошибка, книга не найдена")
            return jsonify({"message": "Книги нет"}), 500
    except Exception as error:   
        print(f"что-то пошло не так: {error}")
        return jsonify({"message":"Ошибка при открытии кники"}), 500 

@liberoom.route('/more', methods=['GET'])
@jwt_required()
def more():
    current_user = get_jwt_identity()
    book_id = request.args.get("book_id")
    print(f"загруженная книга {book_id}")
    if not book_id:
        return jsonify({"message": "book_id не передан"}), 400
    result = get_users_rating(current_user, book_id)
    print(f"result= {result}")
    if result["status"] == "success":
        return jsonify(result), 200
    else:
        print("Ошибка, рейтинга пока нет")
        return jsonify({"message": "Рейтинга пока нет"}), 404
        
@liberoom.route('/more_book', methods=['POST'])
@jwt_required()
def add_book_cat():
    try:
        current_user = get_jwt_identity()
        data = request.json
        cat_id = data.get("cat_id", [])
        book_id = request.args.get("book_id")
        print(f"data: {book_id, cat_id}")
        result = add_cat_book(current_user, cat_id, book_id)
        if result["status"] == "success":
            return jsonify(result), 200
        else:
            print("Ошибка, какая-то ошибка в запросе,")
            return jsonify({"message": "какая-то ошибка"}), 404
    except Exception as error:
        print(f"Ошибка на more_book: {error}")
        return jsonify({"message": str(error)}), 500

@liberoom.route('/rating', methods=['POST']) 
@jwt_required()
def save_rating():
    current_user = get_jwt_identity()
    try:
        data = request.json
        rating = data.get("rating")
        book_id = data.get("book_id")
        if not book_id or rating is None:
            return jsonify({"message": "Не переданы обязательные поля"}), 400
        result = user_rating(current_user, book_id, rating)
        print("Результат user_rating:", result)
        if result["status"] == "success":
            return jsonify(result), 200
        else:
            print("Ошибка сохранения рейтинга")
            return jsonify({"message": "Ошибка при сохранении рейтинга"}), 500
    except Exception as error:
        print(f"Ошибка сервера: {error}")
        return jsonify({"message": "Внутренняя ошибка сервера"}), 500

@liberoom.route('/library', methods=['GET'])
@jwt_required()
def library():
    try:
        current_user = get_jwt_identity()
        result = get_library(current_user)
        if result["status"]=="success":
            return jsonify(result["lib"]), 200
        else:
            return jsonify({"message":"no library yet"})
    except Exception as error:
        print(f"Ошибка: {error}")
        return jsonify({"message":"Внутренняя ошибка сервера"}), 500

@liberoom.route('/library', methods=['DELETE'])
@jwt_required()
def del_cat_id():
    try:
        current_user = get_jwt_identity()
        cat_id = request.args.get("cat_id")
        result = del_cat(current_user, cat_id)
        if result["status"]=="success":
            return jsonify(result), 200
        else:
            return jsonify({"message":"no such cat yet"}), 404
    except Exception as error:
        print(f"Ошибка: {error}")
        return jsonify({"message":"Внутренняя ошибка сервера"}), 500

@liberoom.route('/library/cat', methods=['GET'])
@jwt_required()
def catalog():
    try:
        current_user = get_jwt_identity()
        cat_id = request.args.get("cat_id")
        result = get_catalog(cat_id)
        if result["status"]=="success":
            return jsonify(result["cat"]), 200
        else:
            return jsonify({"message":"no cat yet"})
    except Exception as error:
        print(f"Ошибка: {error}")
        return jsonify({"message":"Внутренняя ошибка сервера"}), 500

@liberoom.route('/library/cat', methods=['DELETE'])
@jwt_required()
def del_from_cat():
    try:
        current_user = get_jwt_identity()
        book_id = request.args.get("book_id")
        cat_id = request.args.get("cat_id")
        result = del_book_cat(book_id, cat_id)
        if result["status"]=="success":
            return jsonify(result), 200
        else:
            return jsonify({"message":"no cat yet"})
    except Exception as error:
        print(f"Ошибка: {error}")
        return jsonify({"message":"Внутренняя ошибка сервера"}), 500

@liberoom.route('/filter', methods=['POST'])
@jwt_required()
def filter():
    try:
        current_user = get_jwt_identity()
        
        data = request.json
        selectedOptions = data.get("selectedOptions", [])
        result = filtering(current_user, selectedOptions)
        if result["status"] =="success":
            return jsonify(result["lib"]), 200
        else:
            return jsonify({"message":"нет книг по таким фильтрам в вашей библиотеке"}), 404
    except Exception as error:
        print(f"Ошибка в filtering: {error}")
        return jsonify({"message":str(error)}), 500

@liberoom.route('/comment', methods=['POST', 'GET'])
@jwt_required()
def comm():
    try:
        current_user = get_jwt_identity()
        if request.method == 'POST':
            data = request.json
            post_text = data.get("post_text")
            book_id = data.get("book_id")
            if not book_id or post_text is None:
                return jsonify({"message": "Не переданы обязательные поля"}), 400

            result = set_comm(current_user, book_id, post_text)
            if result["status"]=="success":
                return jsonify(result), 200
            else:
                return jsonify({"message":"не получилось добавить комментарий"})
        elif request.method == 'GET':
            book_id = request.args.get("book_id")
            result = get_comments(book_id)
            if result["status"] =="success":
                return jsonify(result["comments"]), 200
            else:
                return jsonify({"msg":"no comments"}), 404
    except Exception as error:
        print(f"Ошибка на сервере с запросом comment: {error}")
        return jsonify({"message":str(error)}), 500

@liberoom.route('/comment', methods=['PUT', 'DELETE'])
@jwt_required()
def comm_changes():
    try:
        current_user = get_jwt_identity()
        if request.method == 'PUT':
            data = request.json
            print(f"data {data}")
            comm_id = request.args.get("comm_id")
            comm_text = data.get("comm_text")
            result = update_comm(current_user, comm_id, comm_text)
            if result["status"]=="success":
                return jsonify(result), 200
            else:
                print("ошибка на update comm")
                return jsonify({"msg":"something went wrong in update post"}), 500
        elif request.method == 'DELETE':
            comm_id = request.args.get("comm_id")
            result = del_comm(comm_id, current_user)
            if result["status"]=="success":
                return jsonify(result), 200
            else:
                print("ошибка на delete post")
                return jsonify({"msg":"error on delete post"}), 500
    except Exception as error:
        print(f"Ошибка на запросе в comments: {error}")
        return jsonify({"msg":str(error)}), 500

@liberoom.route('/posts', methods=['GET', 'POST', 'PUT', 'DELETE'])
@jwt_required()
def posts():
    try:
        current_user = get_jwt_identity()
        if request.method == 'GET':
            result = get_posts()
            if result["status"] == "success":
                return jsonify(result["posts"]), 200
            else:
                print(f"Ошибка в get_posts")
                return jsonify({"msg":"что-топошло не так в запросе get_posts"}), 500
        elif request.method == 'POST':
            data = request.json
            post_title = data.get("post_title")
            post_text = data.get("post_text")
            result = add_post(current_user, post_title, post_text)
            if result["status"] == "success":
                return jsonify(result), 200
            else:
                print(f"Ошибка в add_post")
                return jsonify({"msg":"error"}), 500
        elif request.method == 'PUT':
            data = request.json
            print(f"data {data}")
            post_id = request.args.get("post_id")
            post_title = data.get("post_title")
            post_text = data.get("post_text")
            result = update_post(current_user, post_id, post_title, post_text)
            if result["status"]=="success":
                return jsonify(result), 200
            else:
                print("ошибка на update post")
                return jsonify({"msg":"something went wrong in update post"}), 500
        elif request.method == 'DELETE':
            post_id = request.args.get("post_id")
            result = del_post(post_id, current_user)
            if result["status"]=="success":
                return jsonify(result), 200
            else:
                print("ошибка на delete post")
                return jsonify({"msg":"error on delete post"}), 500
    except Exception as error:
        print(f"Ошибка на запросе в posts: {error}")
        return jsonify({"msg":str(error)}), 500

@liberoom.route('/posts/more', methods=['GET'])
@jwt_required()
def post_more():
    try:
        current_user = get_jwt_identity()
        post_id = request.args.get("post_id")
        result = get_post_id(post_id)
        if result["status"] == "success":
            return jsonify(result["post_id"]), 200
        else:
            print(f"Ошибка, пост не найден")
            return jsonify({"message": "Поста нет"}), 404

    except Exception as error:
        print(f"Ошибка на запросе в posts/more: {error}")
        return jsonify({"msg":str(error)}), 500

@liberoom.route('/more_post/comment', methods=['GET', 'POST'])
@jwt_required()
def more_post_comm():
    try:
        current_user = get_jwt_identity()
        if request.method == 'POST':
            data = request.json
            post_text = data.get("post_text")
            post_id = data.get("post_id")
            if not post_id or post_text is None:
                return jsonify({"message": "Не переданы обязательные поля"}), 400

            result = set_comm_post(current_user, post_id, post_text)
            if result["status"]=="success":
                return jsonify(result), 200
            else:
                return jsonify({"message":"не получилось добавить комментарий"})
        elif request.method == 'GET':
            post_id = request.args.get("post_id")
            result = get_comments_post(post_id)
            if result["status"] =="success":
                return jsonify(result["comments"]), 200
            else:
                return jsonify({"msg":"no comments"}), 404
    except Exception as error:
        print(f"Ошибка на сервере с запросом comment: {error}")
        return jsonify({"message":str(error)}), 500

@liberoom.route('/catalog', methods=['POST', 'GET'])
@jwt_required()
def catalog_id():
    try:
        current_user = get_jwt_identity()
        if request.method == 'POST':
            data = request.json
            cat_name = data.get("cat_name")
            print(f"data: {cat_name}")
            result = add_catalog(current_user, cat_name)
            if result["status"] =="success":
                return jsonify(result), 200
            else:
                print("some error at add_cat")
                return jsonify({"msg":"some error in add_catalog"}), 500
        elif request.method == 'GET':
            result = get_cat(current_user)
            if result["status"] =="success":
                return jsonify(result["cat"]), 200
            else:
                return jsonify({"msg":"some error in get_cat"}), 500
    except Exception as error:
        print(f"on catalog: {error}")
        return jsonify({"msg":str(error)}), 500

@liberoom.route('/library/more_cat', methods=['GET'])
@jwt_required()
def cat_more():
    try:
        current_user = get_jwt_identity()
        cat_id = request.args.get("cat_id")
        result = get_cat_id(cat_id)
        if result["status"] == "success":
            return jsonify(result["cat_id"]), 200
        else:
            print(f"Ошибка, категория не найдена")
            return jsonify({"message": "категории нет нет"}), 404
    except Exception as error:
        print(f"on more_cat: {error}")
        return jsonify({"msg":str(error)}), 500

@liberoom.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)  # Требуется рефреш-токен
def refresh():
    try:        
        current_user = get_jwt_identity() 
        print(f"Текущий пользователь: {current_user}")
        response = jsonify({"login": "ok"})
        unset_jwt_cookies(response)
        
        access_token = create_access_token(identity=current_user)
        refresh_token = create_refresh_token(identity=current_user)

        set_access_cookies(response, access_token)
        set_refresh_cookies(response, refresh_token)

        return response, 200
    except Exception as error:
        print(f"Ошибка при обновлении токена: {error}")
        return jsonify({"message": "Ошибка при обновлении токена"}), 500

@liberoom.route('/rec', methods=['GET'])
@jwt_required()
def rec():
    print("запрос на rec здесь")
    current_user = get_jwt_identity()
    try:
        user_id = get_user_id(current_user)
        if user_id["status"] == "success":
            print("user_id there")
            knn_model(user_id["user_id"])
        rec_res = get_rec(current_user)
        if rec_res["status"] == "success":
            print(f"Тип rec_res['rec']: {type(rec_res['rec'])}") #он tuple, внутри 1 лист, внутри листа куча dict
            rec_list = rec_res['rec'][0] #вытащили лист
            book_id_list = [book['item_id'] for book in rec_list]#вытащил value
            
            result = rec_books(book_id_list)  # Ищем книгу в БД
            if result["status"] == "success":            
                return jsonify(result["books"][:20]), 200
        else:
            print("Ошибка поиска рекомендаций")
            return jsonify({"message": "Ошибка при получении рейтинга"}), 500
    except Exception as error:
        print(f"Ошибка при запросе на rec: {error}")
        return jsonify({"message":"Ошибка при запросе на рекомендации"})

@liberoom.route('/some', methods=['GET'])
@jwt_required()
def user():
    try:
        current_user = get_jwt_identity()
        result = get_user_id(current_user)
        if result["status"]=="success":
            return jsonify(result["user_id"])
    except Exception as error:
        return jsonify({"msg":str(error)}), 500

if __name__ == '__main__':
    liberoom.run(debug=True)

#http://localhost:5000
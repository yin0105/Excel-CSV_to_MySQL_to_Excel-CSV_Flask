#!/usr/bin/env python
from flask import Flask, render_template, redirect, url_for
from flask.globals import request #, request, flash, g, session
from flask_bootstrap import Bootstrap
# from models import UserForm, LoginForm
# from flask_datepicker import datepicker
from flask_sqlalchemy import SQLAlchemy
from flask_mysqldb import MySQL
# import json
# from proxy import MyThread, proxy_status, proxies_list
from sqlalchemy_serializer import SerializerMixin
# import requests
# from bs4 import BeautifulSoup
from os.path import join, dirname, realpath
from flask_file_upload.file_upload import FileUpload
import xlrd
# import MySQLdb
# import pprint

class Config(object):
    SECRET_KEY = '78w0o5tuuGex5Ktk8VvVDF9Pw3jv1MVE'

app = Flask(__name__)
app.config.from_object(Config)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/information_schema'
app.config['SECRET_KEY'] = "3489wfksf93r2k3lf9sdjkfe9t2j3krl"
app.config["UPLOAD_FOLDER"] = join(dirname(realpath(__file__)), "static/uploads")
app.config["ALLOWED_EXTENSIONS"] = ["csv", "xls", "xlsx", "xlsm"]
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024  # 100mb

Bootstrap(app)
db = SQLAlchemy(app)
file_upload = FileUpload(app, db)


class Schemata(db.Model, SerializerMixin):  
    __tablename__ = 'schemata'

    serialize_only = ('schema_name')
    
    schema_name =  db.Column(db.String(64), nullable = False, primary_key=True)

    def __init__(self, schema_name):
        self.schema_name = schema_name


class Tables(db.Model, SerializerMixin):  
    __tablename__ = 'TABLES'

    serialize_only = ('table_name', 'table_schema')
    
    table_name =  db.Column(db.String(64), nullable = False, primary_key=True)
    table_schema =  db.Column(db.String(64), nullable = False)

    def __init__(self, table_name, table_schema):
        self.table_name = table_name
        self.table_schema = table_schema


class PostalCode(db.Model, SerializerMixin):  
    __tablename__ = 'state_postal_code'

    serialize_only = ('state')
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    country = db.Column(db.String(50), nullable = False)
    country_code = db.Column(db.String(6), nullable = False)
    state = db.Column(db.String(50), nullable = False) 
    state_code = db.Column(db.String(8), nullable = False)
 
    def __init__(self, country, country_code, state, state_code):
        self.country = country
        self.country_code = country_code
        self.state = state
        self.state_code = state_code

class Proxies(db.Model, SerializerMixin):  
    __tablename__ = 'proxy'

    serialize_only = ('state')
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    proxy = db.Column(db.String(30), nullable = False)
    bad = db.Column(db.Integer, nullable = False)
 
    def __init__(self, proxy, bad):
        self.proxy = proxy
        self.bad = bad


@file_upload.Model
class FileModel(db.Model):
   id = db.Column(db.Integer, primary_key=True)

   my_file = file_upload.Column()


@app.route('/', methods=['GET', 'POST'])
def admin():
    return redirect(url_for('msg', msg=""))


@app.route('/msg', methods=['GET', 'POST'])
def msg(msg=""):
    return render_template('main.html', msg=msg)

# def msg(msg):
    # return render_template('main.html', msg=msg)


@app.route('/get_db_list', methods=['POST'])
def get_db_list(): 
    db_list = Schemata.query.filter(~Schemata.schema_name.in_(['information_schema', 'mysql', 'performance_schema'])).all()
    resp = ""
    for db_name in db_list:
        resp += "<option >" + db_name.schema_name + "</option>"
    return resp


@app.route('/get_tbl_list/<string:db_>', methods=['GET', 'POST'])
def get_tbl_list(db_): 
    tbl_list = Tables.query.filter_by(table_schema=db_).all()
    resp = ""
    for tbl_name in tbl_list:
        resp += "<option >" + tbl_name.table_name + "</option>"
    return resp

    
@app.route('/to_mysql/<string:db_name>/<string:tbl_name>', methods=['GET', 'POST'])
def to_mysql(db_name, tbl_name): 
    sql = "CREATE TABLE " + db_name + ".`" + tbl_name + "` (`id` int(11) NOT NULL AUTO_INCREMENT,  "
    sql_2 = "INSERT INTO " + db_name + ".`" + tbl_name + "`  ("
    if 'f_name' in request.files:
        u_file = request.files['f_name']
        if u_file.filename != '':       
            file_path = join(dirname(realpath(__file__)), "static\\upload", u_file.filename)     
            u_file.save(file_path)

            book = xlrd.open_workbook(file_path)
            sheet = book.sheet_by_index(0)

            # Create Database
            for c in range(sheet.ncols):
                cell_val = sheet.cell(0, c).value                
                if cell_val == "": 
                    col_count = c
                    break

                sql += " `" + cell_val + "` varchar(20) NOT NULL,  "
                sql_2 += " `" + cell_val + "`, " 

            sql = sql[:-2] + "  PRIMARY KEY (`id`)) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"
            sql_2 = sql_2[:-2] + ") VALUES (" + "%s, " * col_count
            sql_2 = sql_2[:-2] + ")"
            result = db.engine.execute(sql)

            # Insert Data
            for r in range(1, sheet.nrows):
                val_arr = []
                for c in range(col_count):
                    val_arr.append(str(sheet.cell(r,c).value))

                db.engine.execute(sql_2, tuple(val_arr))
            
            return redirect(url_for('msg', msg="Successfuly insert into MySQL."))


    # def category_init_func(row):
    #     c = Category(row['name'])
    #     c.id = row['id']
    #     return c
    # def post_init_func(row):
    #     c = Category.query.filter_by(name=row['category']).first()
    #     p = Post(row['title'], row['body'], c, row['pub_date'])
    #     return p
    # request.save_book_to_database(
    #     field_name='f_name', session=db.session,
    #     tables=[],
    #     initializers=[])
    # return redirect(url_for('admin'), code=302)



# @app.route('/login', methods = ['POST', 'GET'])
# def login():
#     # print(request.form['name'] + "::::::" + request.form['password'])
#     if request.method == 'POST':
#         if os.environ.get('ADMIN_NAME') == request.form['name'] and os.environ.get('ADMIN_PASSWORD') == request.form['password']:
#             session['username'] = request.form['name']
#             return redirect(url_for('admin'))
   
#     return render_template('login.html', form=LoginForm())

# @app.route('/logout', methods = ['POST', 'GET'])
# def logout():
#     session.pop("username", None)
#     return redirect(url_for("login"))

# @app.route('/add_user', methods=['GET', 'POST'])
# def add_user():
#     form = UserForm(request.form)
    
#     if 'type_' in request.form:# == "save":

#         if not form.validate_on_submit():
#             flash('Please enter all the fields', 'error')
#         else:
#             str = ''
#             for i in range(len(request.form.getlist('td_search[]'))):
#                 if request.form.getlist('td_search[]')[i]:
#                     if str != '' :
#                         str += ','
#                     str += '{"s": "' + request.form.getlist('td_search[]')[i] +'", '
#                     str += '"m": "' + request.form.getlist('td_miles[]')[i] +'", '
#                     str += '"t": "' + request.form.getlist('td_time[]')[i] +'"}'
#             str = '{"locationList":[' + str +']}'

#             user_ = User(request.form['name'], request.form['user_id'], request.form['password'], request.form['email'], request.form['phone'], request.form['dates'], str)
            
#             db.session.add(user_)
#             db.session.commit()
#             flash('Record was successfully added')
#             return redirect(url_for('admin'))   
    
#     form.locations = [{"search": "", "miles": "", "time": ""}]
#     return render_template('user.html', form=form, )


# @app.route('/edit_user', methods=['POST'])
# def edit_user():  
#     form = UserForm(request.form)
    
#     # if request.method == 'POST':
#     if request.form['type_'] == "save":
#         if not form.validate_on_submit():
#             flash('Please enter all the fields', 'error')
#         else:
#             str = ''
#             for i in range(len(request.form.getlist('td_search[]'))):
#                 if request.form.getlist('td_search[]')[i]:
#                     if str != '' :
#                         str += ','
#                     str += '{"s": "' + request.form.getlist('td_search[]')[i] +'", '
#                     str += '"m": "' + request.form.getlist('td_miles[]')[i] +'", '
#                     str += '"t": "' + request.form.getlist('td_time[]')[i] +'"}'
#             str = '{"locationList":[' + str +']}'
           
            
#             db.session.query(User).filter_by(id = request.form['id']).update({User.name: request.form['name'], User.user_id: request.form['user_id'], User.password: request.form['password'], User.email: request.form['email'], User.phone: request.form['phone'], User.dates: request.form['dates'], User.locations: str}, synchronize_session = False)
#             db.session.commit()
#             flash('Record was successfully updated')
#             return redirect(url_for('admin'))   
#     else:
#         user_ = User.query.filter_by(id=request.form['user_id']).first()
#     user_.locations = json.loads(user_.locations)
#     return render_template('user.html', form=form, user=user_)


# @app.route('/del_user/<int:user_id>', methods=['GET', 'POST'])
# def del_user(user_id):
#     db.session.query(User).filter_by(id=user_id).delete()
#     db.session.commit()

#     return ""


# @app.route('/view_log', methods=['POST'])
# def view_log():  
#     log_list = []
#     try:
#         log_file = open('logs/' + request.form['user_id'] + '.log', 'r') 
#         while True: 
#             line = log_file.readline()                
#             if not line: 
#                 break
#             if line.find("/") < 0:
#                 log_list.append(line.strip())                       
#     except:
#         pass
#     return render_template('log.html', log_list = log_list)


# @app.route('/calendar', methods=['GET', 'POST'])
# def calendar():
#     return render_template('calendar.html')


# @app.route('/ajax_get_user_status', methods=['GET', 'POST'])
# def ajax_get_user_status():
#     users = User.query.order_by(User.name)
#     result = ""
#     for user_ in users:
#         if str(user_.id) in proxy_status:
#             result += str(proxy_status[str(user_.id)]) + ","
#         else:
#             result += "0,"
#     result = result[:-1]

#     return result


# @app.route('/start_proxy/<userId>', methods=['GET', 'POST'])
# def start_proxy(userId):
#     try:
#         if proxy_status[userId] >= 1:
#             return ""
#     except:
#         pass

#     proxy_status[userId] = 1
#     print("proxy_status[" + userId + "] = " + str(proxy_status[userId]))
#     db.session.query(User).filter_by(id = userId).update({User.status: 1}, synchronize_session = False)
#     db.session.commit()

#     user_ = User.query.filter_by(id=userId).first()
#     user_.locations = json.loads(user_.locations)

#     t = MyThread(userId, user_.to_dict())
#     t.start()

#     return ""
        

# @app.route('/stop_proxy/<userId>', methods=['GET', 'POST'])
# def stop_proxy(userId):
#     proxy_status[userId] = 0
#     db.session.query(User).filter_by(id = userId).update({User.status: 0}, synchronize_session = False)
#     db.session.commit()
#     return ""


# def status_initialize():
#     db.session.query(User).update({User.status: 0}, synchronize_session = False)
#     db.session.commit()
#     return


# def get_proxies_list():
#     if os.environ.get('FREE_PROXY') != "true":
#         try:
#             proxies_file = open('proxies.txt', 'r') 
#             while True: 
#                 line = proxies_file.readline()                
#                 if not line: 
#                     break
#                 proxies_list.append(line.strip())
#             print("\n:::::::::::  Paid Proxy  ::::::::\n")
#             return
#         except:
#             pass
#     print("\n:::::::::::  Free Proxy  ::::::::\n")
#     proxies = Proxies.query.filter_by(bad=0)
#     for proxy in proxies:
#         proxies_list.append(proxy.proxy)
#     print(len(proxies_list))
    
#     if len(proxies_list) < 50 :
#         URL = 'https://github.com/TheSpeedX/PROXY-List/blob/master/http.txt'
#         page = requests.get(URL)
#         soup = BeautifulSoup(page.content, 'html.parser')
#         trs = soup.find_all(class_="blob-code blob-code-inner js-file-line")
#         for tr in trs:
#             if tr.get_text()[0] >= '0' and tr.get_text()[0] <= '9':
#                 proxies_list.append(tr.get_text())
#                 proxy = Proxies(tr.get_text(), 0)            
#                 db.session.add(proxy)
#                 db.session.commit()
#     print(len(proxies_list))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5300, debug=True)

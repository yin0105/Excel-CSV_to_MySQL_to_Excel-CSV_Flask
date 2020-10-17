#!/usr/bin/env python
from flask import Flask, render_template, redirect, url_for, Response
from flask.globals import request #, request, flash, g, session
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_mysqldb import MySQL
from sqlalchemy.sql.schema import Column
from sqlalchemy_serializer import SerializerMixin
from os.path import join, dirname, realpath
from flask_file_upload.file_upload import FileUpload
import xlrd, xlwt
import csv
import io


class Config(object):
    SECRET_KEY = '78w0o5tuuGex5Ktk8VvVDF9Pw3jv1MVE'

app = Flask(__name__)
app.config.from_object(Config)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/'
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


class Columns(db.Model, SerializerMixin):  
    __tablename__ = 'COLUMNS'

    serialize_only = ('column_name', 'table_name', 'table_schema')
    
    column_name =  db.Column(db.String(64), nullable = False, primary_key=True)
    table_name =  db.Column(db.String(64), nullable = False)
    table_schema =  db.Column(db.String(64), nullable = False)

    def __init__(self, column_name, table_name, table_schema):
        self.column_name = column_name
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


@app.route('/get_db_list', methods=['POST'])
def get_db_list(): 
    # db_list = Schemata.query.filter(~Schemata.schema_name.in_(['information_schema', 'mysql', 'performance_schema'])).all()
    db_list = db.engine.execute("SHOW DATABASES")
    resp = ""
    for db_name in db_list:
        if db_name.Database in ['information_schema', 'mysql', 'performance_schema'] : continue
        resp += "<option >" + db_name.Database + "</option>"
    return resp


@app.route('/get_tbl_list/<string:db_>', methods=['GET', 'POST'])
def get_tbl_list(db_): 
    # tbl_list = Tables.query.filter_by(table_schema=db_).all()
    db.engine.execute("USE " + db_)
    tbl_list = db.engine.execute("SHOW TABLES")
    resp = ""
    for row in tbl_list:
        for tbl_name in row:
            resp += "<option >" + tbl_name + "</option>"
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
            file_ext = u_file.filename[-3:]
            if file_ext.lower() == "csv":
                with open(file_path, 'r') as in_file:
                    csv_file = csv.DictReader(in_file)
                    col_count = len(csv_file.fieldnames)
                    for c in csv_file.fieldnames:
                        sql += " `" + c + "` varchar(20) NOT NULL,  "
                        sql_2 += " `" + c + "`, " 

                    sql = sql[:-2] + "  PRIMARY KEY (`id`)) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"
                    sql_2 = sql_2[:-2] + ") VALUES (" + "%s, " * col_count
                    sql_2 = sql_2[:-2] + ")"
                    result = db.engine.execute(sql)


                    first_row = True
                    for row in csv_file:
                        if first_row:
                            first_row = False
                            continue
                        val_arr = []
                        for c in row:
                            val_arr.append(str(row[c]))

                        db.engine.execute(sql_2, tuple(val_arr))
                in_file.close()
            else:
                book = xlrd.open_workbook(file_path)
                sheet = book.sheet_by_index(0)
                col_count = sheet.ncols
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


@app.route('/to_excel/<string:db_name>/<string:tbl_name>', methods=['GET', 'POST'])
def to_excel(db_name, tbl_name):
    # col_list = Columns.query.filter(Columns.table_schema==db_name, Columns.table_name==tbl_name).all()
    col_list = db.engine.execute("SHOW COLUMNS FROM " + db_name + ".`" + tbl_name + "`")
    output = io.BytesIO()
	
    #create WorkBook object
    workbook = xlwt.Workbook()
	
    #add a sheet
    sh = workbook.add_sheet('Sheet1')
    col_index = 0
    sql = "SELECT "
    for col in col_list:
        if col.Field != "id":	
            sh.write(0, col_index, col.Field)
            sql += "`" + col.Field + "`, "
            col_index += 1
    sql = sql[:-2] + " FROM " + db_name + ".`" + tbl_name + "`"
    print("sql= " + sql)
    result = db.engine.execute(sql)
    r = 0
    for row in result:
        r += 1
        c = 0
        for cell in row:
            sh.write(r, c, cell)
            c += 1

	#add headers

    workbook.save(output)
    output.seek(0)

    return Response(output, mimetype="application/ms-excel", headers={"Content-Disposition":"attachment;filename=" + tbl_name + ".xls"})
        

@app.route('/to_csv/<string:db_name>/<string:tbl_name>', methods=['GET', 'POST'])
def to_csv(db_name, tbl_name):
    # col_list = Columns.query.filter(Columns.table_schema==db_name, Columns.table_name==tbl_name).all()
    col_list = db.engine.execute("SHOW COLUMNS FROM " + db_name + ".`" + tbl_name + "`")
    output = io.StringIO()	
    writer = csv.writer(output)
	
    #add a sheet
    sql = "SELECT "
    col_arr = []
    for col in col_list:
        if col.Field != "id":	
            col_arr.append(col.Field)
            sql += "`" + col.Field + "`, "
    writer.writerow(col_arr)
    sql = sql[:-2] + " FROM " + db_name + ".`" + tbl_name + "`"
    result = db.engine.execute(sql)

    for row in result:
        col_arr = []
        for cell in row:
            col_arr.append(str(cell))
        writer.writerow(col_arr)

	#add headers
    output.seek(0)

    return Response(output, mimetype="text/csv", headers={"Content-Disposition":"attachment;filename=" + tbl_name + ".csv"})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5300, debug=True)

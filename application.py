import os
import datetime
import csv
import collections
import pandas as pd
import math
import random
import io

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session, Response, send_file, url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from helpers import apology, login_required, calculate_wqi_obs, assign_class, replace_str

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# we will store the uploaded files
UPLOAD_FOLDER = '/home/ubuntu/project/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///wql.db")

# GLOBAL variables
#user_id = int(session.get("user_id"))

@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route("/enter", methods=["GET", "POST"])
@login_required
def enter():
    #create table if it doesnt exist
    #db.execute("CREATE TABLE IF NOT EXISTS data (id INT,site_id VARCHAR(255),date TEXT,lat REAL,lon REAL,arsenic REAL,cd REAL,cod REAL,cr REAL,do REAL,ecoli REAL,fluoride REAL, nh3 REAL,no2 REAL,no3 REAL,pb REAL,po4 REAL,turbidity REAL, wqi REAL")
    user_id = int(session.get("user_id"))
    if request.method == "GET":
        #TODO
        return render_template("enter.html")
        #return apology("apology", 403)

    else:
        #attributes
        site_id=request.form.get("site_id")
        date=request.form.get("date")
        lat=request.form.get("lat")
        lon=request.form.get("lon")

        #wql data
        arsenic=request.form.get("arsenic")
        cd=request.form.get("cd")
        cod=request.form.get("cod")
        cr=request.form.get("cr")
        do=request.form.get("do")
        ecoli=request.form.get("ecoli")
        fluoride=request.form.get("fluoride")
        nh3=request.form.get("nh3")
        no2=request.form.get("no2")
        no3=request.form.get("no3")
        pb=request.form.get("pb")
        po4=request.form.get("po4")
        turbidity=request.form.get("turbidity")

        db.execute("CREATE TABLE IF NOT EXISTS data (rowid INTEGER PRIMARY KEY,id INT,site_id VARCHAR(255),\
        date TEXT,lat REAL,lon REAL,\
        arsenic REAL,cd REAL,cod REAL,cr REAL,do REAL,ecoli REAL,fluoride REAL, nh3 REAL,no2 REAL,\
        no3 REAL,pb REAL,po4 REAL,turbidity REAL, \
        wqi REAL, class_nonwt VARCHAR(255), wqi_wt REAL,class_wt VARCHAR(255))")

        #create dict
        wqi_dict = {'arsenic':arsenic,'cd':cd,'cod':cod,'cr':cr,'do':do,'ecoli':ecoli,'fluoride':fluoride,
        'nh3':nh3,'no2':no2,'no3':no3,'pb':pb,'po4':po4,'turbidity':turbidity}
        for k in wqi_dict.keys():
            if wqi_dict[k] == '' or wqi_dict[k] == None: #if no values entered in textbox
                wqi_dict[k] = None
            else: #if values entered in textbox
                wqi_dict[k] = float(wqi_dict[k])

        #weights
        weights = {"arsenic": 5, "cd":5,"cod":3, "cr":5,"do":4,"ecoli":3,"fluoride":3,"nh3":3,"no2":2,
        "no3":2, "pb":5,"po4":2,"turbidity":4}
        weights_equal = {"arsenic": 1, "cd":1,"cod":1, "cr":1,"do":1,"ecoli":1,"fluoride":1,"nh3":1,"no2":1,
        "no3":1, "pb":1,"po4":2,"turbidity":1}

        #wql standards classes
        #wqi_wt_class = [0, 13.94,14.21,18.42,71.84,100]
        #wqi_class = [0,16.15,18.46,24.61,76.15,100]

        wqi_wt, class_wqi_wt = assign_class(wqi_dict,weights)
        wqi, class_wqi = assign_class(wqi_dict,weights_equal)

        db.execute("INSERT INTO data (id,site_id,date,lat,lon,arsenic,cd,cod,cr,do,ecoli,fluoride,nh3,no2,\
        no3,pb,po4,turbidity,wqi,class_nonwt,wqi_wt,class_wt) \
        VALUES (:id,:site_id,:date,:lat,:lon,:arsenic,:cd,:cod,:cr,:do,:ecoli,:fluoride,:nh3,:no2,\
        :no3,:pb,:po4,:turbidity,:wqi,:class_nonwt,:wqi_wt,:class_wt)",
        id=user_id,site_id=site_id,date=date,lat=lat,lon=lon,arsenic=arsenic,cd=cd,cod=cod,cr=cr,
        do=do,ecoli=ecoli,fluoride=fluoride,nh3=nh3,no2=no2,no3=no3,pb=pb,po4=po4,turbidity=turbidity,
        wqi=wqi, class_nonwt=class_wqi, wqi_wt=wqi_wt, class_wt=class_wqi_wt)

        missing_parameters = [] #get a list of missing values
        for k in wqi_dict.keys():
            if wqi_dict[k] is None:
                missing_parameters.append(k)

        return render_template("entered.html",missing_parameters=missing_parameters,
        wqi=wqi,wqi_wt=wqi_wt,class_wqi=class_wqi, class_wqi_wt=class_wqi_wt)

@app.route("/csv", methods=["GET", "POST"])
@login_required
def upload_csv():
    user_id = int(session.get("user_id"))

    if request.method == "GET":
        return render_template("csv.html")

    else:
        get_file=request.files['file']
        if not get_file: #if file not submitted
            return apology("File not uploaded", 403)
        if get_file.filename.rsplit('.', 1)[1].lower() != 'csv': #if file extension not csv
            return apology("Please upload a csv file", 403)
        else:
            get_file=request.files['file']
            filename = secure_filename(get_file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            get_file.save(filepath)
            print(filepath)


            #file_contents = get_file.stream.read().decode("utf-8")
            #file_contents = io.StringIO(get_file.stream.read().decode("UTF8"), newline=None)
            #csv_input = csv.reader(file_contents)
            with io.open(filepath, "r", encoding='utf-8-sig') as file:
                csv_input = csv.DictReader(file)
            #csv_input = csv.DictReader(open(file_contents))
                for row in csv_input:
                    print(row)
                    #row = {k.lower():v for k,v in row.items()} #change all keys to lower case
                    site_id = row["site_id"]
                    date = row["date"]
                    lat = float(row["lat"])
                    lon = float(row["lon"])
                    arsenic = float(row["arsenic"])
                    cd = float(row["cd"])
                    cr = float(row["cr"])
                    cod = float(row["cod"])
                    do = float(row["do"])
                    ecoli = float(row["ecoli"])
                    fluoride = float(row["fluoride"])
                    nh3 = float(row["nh3"])
                    no2 = float(row["no2"])
                    no3 = float(row["no3"])
                    pb = float(row["pb"])
                    po4 = float(row["po4"])
                    turbidity = float(row["turbidity"])

                    #create dict
                    wqi_dict = {'arsenic':arsenic,'cd':cd,'cod':cod,'cr':cr,'do':do,'ecoli':ecoli,'fluoride':fluoride,
                    'nh3':nh3,'no2':no2,'no3':no3,'pb':pb,'po4':po4,'turbidity':turbidity}
                    for k in wqi_dict.keys():
                        if wqi_dict[k] == '' or wqi_dict[k] == None: #if no values entered in textbox
                            wqi_dict[k] = None
                        else: #if values entered in textbox
                            wqi_dict[k] = float(wqi_dict[k])

                    #weights
                    weights = {"arsenic": 5, "cd":5,"cod":3, "cr":5,"do":4,"ecoli":3,"fluoride":3,"nh3":3,"no2":2,"no3":2, "pb":5,"po4":2,"turbidity":4}
                    weights_equal = {"arsenic": 1, "cd":1,"cod":1, "cr":1,"do":1,"ecoli":1,"fluoride":1,"nh3":1,"no2":1,"no3":1, "pb":1,"po4":2,"turbidity":1}

                    wqi_wt, class_wqi_wt = assign_class(wqi_dict,weights)
                    wqi, class_wqi = assign_class(wqi_dict,weights_equal)

                    db.execute("INSERT INTO data (id,site_id,date,lat,lon,arsenic,cd,cod,cr,do,ecoli,fluoride,nh3,no2,\
                    no3,pb,po4,turbidity,wqi,class_nonwt,wqi_wt,class_wt) \
                    VALUES (:id,:site_id,:date,:lat,:lon,:arsenic,:cd,:cod,:cr,:do,:ecoli,:fluoride,:nh3,:no2,\
                    :no3,:pb,:po4,:turbidity,:wqi,:class_nonwt,:wqi_wt,:class_wt)",
                    id=user_id,site_id=site_id,date=date,lat=lat,lon=lon,arsenic=arsenic,cd=cd,cod=cod,cr=cr,
                    do=do,ecoli=ecoli,fluoride=fluoride,nh3=nh3,no2=no2,no3=no3,pb=pb,po4=po4,turbidity=turbidity,
                    wqi=wqi, class_nonwt=class_wqi, wqi_wt=wqi_wt, class_wt=class_wqi_wt)

            return redirect("/data")
            #return render_template("csv.html")

@app.route("/map")
@login_required
def map():
    user_id = int(session.get("user_id"))
    data = db.execute("SELECT * FROM data WHERE id = :user_id", user_id=user_id)

    if len(data) == 0:
        return apology("No data entered yet", 403)

    for k,v in data[1].items():
        if k == 'lat':
            lat = v
        if k =='lon':
            lon = v

    df = pd.DataFrame(data)
    grouped = df.fillna(0.00001).groupby(['site_id'])
    avg = grouped.mean()
    avg_dict = avg.to_dict('index') #{index -> {column -> value}}
    for k,v in avg_dict.items():
            latitude = v['lat']
            longitude = v['lon']
            columns_remove = ['rowid','id','lat','lon','wqi','wqi_wt']
            for item in columns_remove:
                v.pop(item,None)
            weights = {"arsenic": 5, "cd":5,"cod":3, "cr":5,"do":4,"ecoli":3,"fluoride":3,"nh3":3,"no2":2,"no3":2, "pb":5,"po4":2,"turbidity":4}
            weights_equal = {"arsenic": 1, "cd":1,"cod":1, "cr":1,"do":1,"ecoli":1,"fluoride":1,"nh3":1,"no2":1,"no3":1, "pb":1,"po4":2,"turbidity":1}
            wqi_wt, class_wqi_wt = assign_class(v,weights)
            wqi, class_wqi = assign_class(v,weights_equal)
            v['wqi'] = wqi
            v['wqi_wt'] = wqi_wt
            v['class_nonwt'] = class_wqi
            v['class_wt'] = class_wqi_wt
            v['lat'] = latitude
            v['lon'] = longitude


    return render_template("map.html",data=data,lat=lat,lon=lon,avg_dict=avg_dict)
    #return apology("apology", 403)

@app.route("/data", methods=["GET", "POST"])
@login_required
def data():
    user_id = int(session.get("user_id"))

    if request.method == "GET":
        data = db.execute("SELECT * FROM data WHERE id = :user_id", user_id=user_id)

        for item in data:
            item['site_id'] = item['site_id'].upper()

        return render_template("history.html",data=data)

    else:
        delete_rowid = request.form.get("delete")
        db.execute("DELETE FROM data WHERE rowid = :rowid",rowid=delete_rowid)
        data = db.execute("SELECT * FROM data WHERE id = :user_id", user_id=user_id)
        return render_template("history.html",data=data)

@app.route("/delete_all", methods=["POST"])
@login_required
def delete_all():
    user_id = int(session.get("user_id"))
    db.execute("DELETE FROM data WHERE id = :user_id", user_id=user_id)
    return redirect("/data")

@app.route("/getCSV", methods=["GET", "POST"])
@login_required
def getCSV():

    if request.method == "POST":
        user_id = int(session.get("user_id"))
        data = db.execute("SELECT * FROM data WHERE id = :user_id", user_id=user_id)
        for item in data:
            item.pop('rowid',None)

        title = data[0].keys() #get first row's key aka title

        with open('output.csv', 'w') as output_file:
            dict_writer = csv.DictWriter(output_file, title)
            dict_writer.writeheader()
            dict_writer.writerows(data)

        return send_file('output.csv',
                     mimetype='text/csv',
                     attachment_filename='output.csv',
                     as_attachment=True)
        #return Response(output.csv,mimetype="text/csv",headers={"Content-disposition":"attachment; filename=output.csv"})

    else:
        return redirect("/data")

@app.route("/documentation", methods=["GET", "POST"])
@login_required
def documentation():
    if request.method == "GET":
        #with open('breaks.csv', 'r') as output_file:
            #output = csv.DictReader(output_file)
            #list_breaks = list(output)
        breaks_df = pd.read_csv("breaks.csv")
        breaks_column = list(breaks_df.columns)
        renamed_para = replace_str(list(breaks_df['Parameters']))
        breaks_df['Parameters'] = pd.Series(renamed_para)
        breaks_df = breaks_df.set_index('Parameters')
        breaks_df = breaks_df.transpose()
        list_breaks = breaks_df.to_dict()



        with open('wql_std.csv', 'r') as wql_std:
            output = csv.DictReader(wql_std)
            list_wql_std = list(output)

        return render_template("documentation.html",list_breaks=list_breaks,
        breaks_column=breaks_column,
        list_wql_std=list_wql_std)

    else:
        return send_file('breaks.csv',
                     mimetype='text/csv',
                     attachment_filename='breaks.csv',
                     as_attachment=True)

@app.route("/graphs")
@login_required
def graphs():
    user_id = int(session.get("user_id"))
    data = db.execute("SELECT * FROM data WHERE id = :user_id", user_id=user_id)

    if len(data) == 0:
        return apology("No data entered yet", 403)

    for row in data:
        row['site_id'] = row['site_id'].lower() #convert all site names to lower case for grouping
        for k,v in row.items():
            if v=='': #if empty, change to None
                row[k] = None

    num_classes=[]
    num_classes_wt=[]
    for item in data:
        num_classes.append(item['class_nonwt'])
        num_classes_wt.append(item['class_wt'])

    def count_freq(num_classes):
        freq_classes = collections.Counter(num_classes) #returns a dictionary
        freq_classes = collections.OrderedDict(sorted(freq_classes.items())) #sort a dictionary
        return freq_classes

    freq_classes = count_freq(num_classes)
    freq_classes_wt = count_freq(num_classes_wt)

    def rgb_colour(freq_classes):
        classes_colour = {}
        for row in freq_classes.keys():
            if row == "['Class 1']":
                classes_colour['Class 1'] = "rgba(0,0,255,0.4)"
            elif row == "['Class 2']":
                classes_colour['Class 2'] = "rgba(0,255,255,0.4)"
            elif row == "['Class 3']":
                classes_colour['Class 3'] = "rgba(0,255,0,0.4)"
            elif row == "['Class 4']":
                classes_colour['Class 4'] = "rgba(255,255,0,0.4)"
            else:
                classes_colour['Class 5'] = "rgba(255,0,0,0.4)"

        return list(classes_colour.values()) #returns list

    rgb = rgb_colour(freq_classes)
    rgb_wt = rgb_colour(freq_classes_wt)

    df = pd.DataFrame(data)
    grouped = df.fillna(0.00001).groupby(['site_id'])
    avg = grouped.mean()
    avg_list = [{"site_id":r.upper(), "avg_wqi": kv[17],"avg_wqi_wt": kv[18]} for r,kv in avg.iterrows()]

    wql_parameters= list(avg.columns)

    parameters_remove = ['rowid','id','lat','lon','wqi','wqi_wt']
    for item in parameters_remove:
        wql_parameters.remove(item)

    avg_dict = avg.to_dict('index')
    sites_list = avg_dict.keys() #labels for radar data
    datasets_list = []

    for k,v in avg_dict.items():
        columns_remove = ['rowid','id','lat','lon','wqi','wqi_wt']
        for item in columns_remove:
            v.pop(item,None)
        wql_parameters = list(v.keys())
        log_values = [round(math.log10(values),2) for values in v.values()]
        v['data'] = log_values #log_values is a list
        rgb2 = [str(random.randrange(256)),str(random.randrange(256)),str(random.randrange(256)),'0.4']
        rgb1 = ','.join(rgb2)
        rgb_background = ''.join(['rgba(',rgb1,')'])
        rgb_border = ''.join(['rgba(',rgb1,')'])
        v['backgroundColor'] = rgb_background
        v['borderColor'] = rgb_border.replace('0.4','1')
        v['label'] = k
        datasets = {'label':v['label'].upper(), 'backgroundColor':v['backgroundColor'], 'borderColor':v['borderColor'], 'data':v['data']}
        datasets_list.append(datasets)

    wql_parameters = replace_str(wql_parameters)

    df1 = df[['site_id','date','wqi','wqi_wt']] #select columns from df
    site_df = df1.set_index('site_id')
    site_dict = {k: g.to_dict('r') for k,g in site_df.groupby(level=0)} #use groupby so df.to_dict doesnt remove duplicate index
    #For each group, convert this into a dictionary using the "records" or 'r' orient:
    time_nest_list = []
    for sites, lists in site_dict.items():
        rgb2 = [str(random.randrange(256)),str(random.randrange(256)),str(random.randrange(256)),'0.4']
        rgb1 = ','.join(rgb2)
        rgb_background = ''.join(['rgba(',rgb1,')'])
        datasets = {'label':sites,'backgroundColor':rgb_background,'borderColor':rgb_background,'data':lists}
        time_nest_list.append(datasets)

    date_list = list(df['date'])

    def date_format(date_string):
        date_object = datetime.datetime.strptime(date_string,'%d/%m/%Y')
        return date_object

    date_test = [date_format(d) for d in date_list]

    min_date = min(date_test)#.strftime('%d/%m/%Y')
    max_date = max(date_test)#.strftime('%d/%m/%Y')

    step = datetime.timedelta(days=1)

    time_seq = []

    while min_date < max_date:
        time_seq.append(min_date.strftime('%d/%m/%Y'))
        min_date += step

    return render_template("graphs.html",
    freq_classes=freq_classes,freq_classes_wt=freq_classes_wt,
    rgb=rgb,rgb_wt=rgb_wt,
    avg_list=avg_list,
    wql_parameters=wql_parameters, datasets_list=datasets_list,
   time_nest_list = time_nest_list,
   time_seq=time_seq)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted, implement one for if username matches database
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        #ensure confirmation password was submitted
        elif not request.form.get("confirmation"):
            return apology("must provide confirmation password", 403)

        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("Password do not match", 403)

        # Query database for username
        db.execute("INSERT INTO users (username, hash) VALUES (:username, :pw)",
                          username=request.form.get("username"),
                          pw = generate_password_hash(request.form.get("password")))

        # Redirect user to home page
        return render_template("register_success.html")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)



# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
from django.shortcuts import render
from django.template import RequestContext
from django.contrib import messages
from django.http import HttpResponse
from django.conf import settings
import os
import io
import base64
import matplotlib.pyplot as plt
import pymysql
import seaborn as sns
import numpy as np
import pandas as pd
from sklearn.metrics import r2_score
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import MinMaxScaler
from datetime import datetime
from datetime import date
from sklearn.metrics import mean_squared_error
from sklearn.metrics import mean_absolute_error
from math import sqrt
import smtplib

global username, dataset, label_encoder, rf, scaler, usertype

dataset = pd.read_csv("Dataset/Blood.csv")
label_encoder = []
columns = dataset.columns
types = dataset.dtypes.values
for j in range(len(types)):#loop and check each column for non-numeric values
    name = types[j]
    if name == 'object': #finding column with object type
        le = LabelEncoder()
        dataset[columns[j]] = pd.Series(le.fit_transform(dataset[columns[j]].astype(str)))#encode all str columns to numeric
        label_encoder.append([columns[j], le])
dataset.fillna(dataset.mean(), inplace = True)#replace missing values with 0

Y = dataset['demand_units'].ravel()
dataset.drop(['demand_units'], axis = 1,inplace=True)#remove irrelevant columns
X = dataset.values

scaler = MinMaxScaler((0,1))
X = scaler.fit_transform(X)

X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size=0.2)
data = np.load("model/data.npy", allow_pickle=True)
X_train, X_test, y_train, y_test = data

rf = RandomForestRegressor()
rf.fit(X_train, y_train)
predict = rf.predict(X_test)
r2_score = r2_score(y_test, predict)
rmse = sqrt(mean_squared_error(y_test, predict))
mae = mean_absolute_error(y_test, predict)

def getContact(name):
    contact = ""
    location = ""
    con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'lifelink',charset='utf8')
    with con:
        cur = con.cursor()
        cur.execute("select contact,area_location FROM register where username='"+name+"'")
        rows = cur.fetchall()
        for row in rows:
            contact = row[0]
            location = row[1]
            break
    return contact, location

def ViewDonation(request):
    if request.method == 'GET':
        global username
        output='<table border=1 align=center width=100%><tr><th><font size="3" color="black">Blood Bank</th><th><font size="3" color="black">Donor Name</th>'
        output += '<th><font size="3" color="black">Volume Donated</th><th><font size="3" color="black">Blood Type</th><th><font size="3" color="black">Donation Date</th>'
        output += '<th><font size="3" color="black">Expiry Date</th></tr>'
        con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'lifelink',charset='utf8')
        with con:
            cur = con.cursor()
            cur.execute("select * from donation where donor_name='"+username+"'")
            rows = cur.fetchall()
            for row in rows:
                output += '<td><font size="3" color="black">'+row[0]+'</td><td><font size="3" color="black">'+row[1]+'</td><td><font size="3" color="black">'+str(row[2])+'</td>'
                output += '<td><font size="3" color="black">'+row[3]+'</td><td><font size="3" color="black">'+row[4]+'</td><td><font size="3" color="black">'+row[5]+'</td></tr>'
        output+= "</table></br></br></br></br>"
        context= {'data':output}
        return render(request, 'DonorScreen.html', context)

def PatientSearchAction(request):
    if request.method == 'POST':
        btype = request.POST.get('t1', False)
        plate = request.POST.get('t2', False)
        output='<table border=1 align=center width=100%><tr><th><font size="3" color="black">Blood Bank</th><th><font size="3" color="black">Blood Type</th>'
        output += '<th><font size="3" color="black">Available Quantity</th><th><font size="3" color="black">Contact No</th><th><font size="3" color="black">Location Name</th></tr>'
        con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'lifelink',charset='utf8')
        with con:
            cur = con.cursor()
            cur.execute("select * from inventory where blood_type='"+btype+"'")
            rows = cur.fetchall()
            for row in rows:
                contact, location = getContact(row[0])
                output += '<td><font size="3" color="black">'+row[0]+'</td><td><font size="3" color="black">'+row[1]+'</td><td><font size="3" color="black">'+str(row[2])+'</td>'
                output += '<td><font size="3" color="black">'+contact+'</td><td><font size="3" color="black">'+location+'</td></tr>'
        output+= "</table></br></br></br></br>"
        context= {'data':output}
        return render(request, 'PatientScreen.html', context) 

def PatientSearch(request):
    if request.method == 'GET':
       return render(request, 'PatientSearch.html', {})

def sendEmail(em, btype, plate):
    msg = "Urgent required "+btype+" Blood with number of platelets as "+plate
    print(em)
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as connection:
        email_address = 'kaleem202120@gmail.com'
        email_password = 'xyljzncebdxcubjq'
        connection.login(email_address, email_password)
        connection.sendmail(from_addr="kaleem202120@gmail.com", to_addrs=em, msg="Subject : Alert from LIFELINK\n"+msg)

def getEmail(name):
    email = ""
    donor = ""
    con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'lifelink',charset='utf8')
    with con:
        cur = con.cursor()
        cur.execute("select donor_name FROM donation where username='"+name+"'")
        rows = cur.fetchall()
        for row in rows:
            donor = row[0]
            break

    con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'lifelink',charset='utf8')
    with con:
        cur = con.cursor()
        cur.execute("select email FROM register where username='"+donor+"'")
        rows = cur.fetchall()
        for row in rows:
            email = row[0]
            break    
    return email       

def SearchBloodAction(request):
    if request.method == 'POST':
        emails = []
        btype = request.POST.get('t1', False)
        plate = request.POST.get('t2', False)
        output='<table border=1 align=center width=100%><tr><th><font size="3" color="black">Blood Bank</th><th><font size="3" color="black">Blood Type</th>'
        output += '<th><font size="3" color="black">Available Quantity</th><th><font size="3" color="black">Contact No</th><th><font size="3" color="black">Location Name</th></tr>'
        con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'lifelink',charset='utf8')
        with con:
            cur = con.cursor()
            cur.execute("select * from inventory where blood_type='"+btype+"'")
            rows = cur.fetchall()
            for row in rows:
                contact, location = getContact(row[0])
                email = getEmail(row[0])
                emails.append(email)
                output += '<td><font size="3" color="black">'+row[0]+'</td><td><font size="3" color="black">'+row[1]+'</td><td><font size="3" color="black">'+str(row[2])+'</td>'
                output += '<td><font size="3" color="black">'+contact+'</td><td><font size="3" color="black">'+location+'</td></tr>'
        output+= "</table></br></br></br></br>"
        sendEmail(emails, btype, plate)
        context= {'data':output}
        return render(request, 'HospitalScreen.html', context) 

def SearchBlood(request):
    if request.method == 'GET':
       return render(request, 'SearchBlood.html', {})

def Optimize(request):
    if request.method == 'GET':
        output='<table border=1 align=center width=100%><tr><th><font size="3" color="black">Donor Name</th><th><font size="3" color="black">Optimize Donor Engagement</th>'
        output += '<th><font size="3" color="black">Contact No</th></tr>'
        donors = []
        con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'lifelink',charset='utf8')
        with con:
            cur = con.cursor()
            cur.execute("select donor_name FROM donation")
            rows = cur.fetchall()
            for row in rows:
                if row[0] not in donors:
                    donors.append(row[0])
        for i in range(len(donors)):
            con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'lifelink',charset='utf8')
            with con:
                cur = con.cursor()
                cur.execute("select max(donate_date) from donation where donor_name='"+donors[i]+"'")
                rows = cur.fetchall()
                for row in rows:
                    contact, location = getContact(donors[i])
                    last_date = row[0]
                    date1 = datetime.strptime(last_date, "%Y-%m-%d")
                    date2 = datetime.strptime(str(date.today()), "%Y-%m-%d")
                    delta = date2 - date1
                    days = delta.days
                    if days >= 90:
                        msg = "<font size=4 color=green>Eligible to Donate</font>"
                    else:
                        msg = "<font size=4 color=red>NOT Eligible to Donate</font>"
                    output += '<td><font size="3" color="black">'+donors[i]+'</td><td><font size="3" color="black">'+msg+'</td><td><font size="3" color="black">'+contact+'</td>'
                    output += '</tr>'
        output+= "</table></br></br></br></br>"
        context= {'data':output}
        return render(request, 'BankScreen.html', context) 

def ForecastAction(request):
    if request.method == 'POST':
        global rf, scaler, label_encoder
        btype = request.POST.get('t1', False)
        day = request.POST.get('t2', False)
        month = request.POST.get('t3', False)
        year = request.POST.get('t4', False)
        data = []
        data.append([btype, day, int(month.strip()), int(year)])
        data = pd.DataFrame(data,columns=['blood_type','day_of_week','month','year'])
        for i in range(len(label_encoder)):#label encoding from non-numeric to numeric
            le = label_encoder[i]
            data[le[0]] = pd.Series(le[1].transform(data[le[0]].astype(str)))#encode all str columns to numeric
        data = data.values 
        data = scaler.transform(data)
        predict = rf.predict(data).ravel()[0]
        output = "<font size=4 color=blue>Forecasted Demand Based on Selected Input = "+str(round(predict,2))+" Ltrs</font>"
        context= {'data':output}
        return render(request, 'BankScreen.html', context)         

def Forecast(request):
    if request.method == 'GET':
       return render(request, 'Forecast.html', {})

def updateQuantity(username, btype, volume):
    exists = 0
    con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'lifelink',charset='utf8')
    with con:
        cur = con.cursor()
        cur.execute("select username FROM inventory where username='"+username+"'")
        rows = cur.fetchall()
        for row in rows:
            exists = 1
            break
    if exists == 1:
        db_connection = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'lifelink',charset='utf8')
        db_cursor = db_connection.cursor()
        student_sql_query = "update inventory set quantity=quantity+"+volume+" where username='"+username+"' and blood_type='"+btype+"'"
        db_cursor.execute(student_sql_query)
        db_connection.commit()    
    else:
        db_connection = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'lifelink',charset='utf8')
        db_cursor = db_connection.cursor()
        student_sql_query = "INSERT INTO inventory VALUES('"+username+"','"+btype+"','"+volume+"')"
        db_cursor.execute(student_sql_query)
        db_connection.commit()

def ReleaseBloodAction(request):
    if request.method == 'POST':
        global username
        hospital = request.POST.get('t1', False)
        patient = request.POST.get('t2', False)
        btype = request.POST.get('t3', False)
        volume = request.POST.get('t4', False)
        dd = str(date.today())
        volume = float(volume)
        avail = 0
        con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'lifelink',charset='utf8')
        with con:
            cur = con.cursor()
            cur.execute("select quantity FROM inventory where username='"+username+"' and blood_type='"+btype+"'")
            rows = cur.fetchall()
            for row in rows:
                avail = row[0]
                break
        if avail > volume:
            db_connection = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'lifelink',charset='utf8')
            db_cursor = db_connection.cursor()
            student_sql_query = "update inventory set quantity=quantity-"+str(volume)+" where username='"+username+"' and blood_type='"+btype+"'"
            db_cursor.execute(student_sql_query)
            db_connection.commit()
            db_connection = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'lifelink',charset='utf8')
            db_cursor = db_connection.cursor()
            student_sql_query = "INSERT INTO releaseBlood VALUES('"+hospital+"','"+patient+"','"+btype+"','"+str(volume)+"','"+dd+"','"+username+"')"
            db_cursor.execute(student_sql_query)
            db_connection.commit()
            avail = str(volume)+" successfully released to "+hospital
        else:
            avail = "<font size3 color=red>Insufficient Blood Volume to release</font>"
        context= {'data':avail}
        return render(request, 'BankScreen.html', context)    
            

def ReleaseBlood(request):
    if request.method == 'GET':
        output = '<tr><td><font size="3" color="black">Choose&nbsp;Donor</td><td><select name="t1">'
        con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'lifelink',charset='utf8')
        with con:
            cur = con.cursor()
            cur.execute("select username FROM register where usertype='Hospital'")
            rows = cur.fetchall()
            for row in rows:
                output += '<option value="'+row[0]+'">'+row[0]+'</option>'
        output += '</select></td></tr>'        
        context= {'data1':output}
        return render(request, 'ReleaseBlood.html', context)        

def DonationDriveAction(request):
    if request.method == 'POST':
        global username
        donor = request.POST.get('t1', False)
        volume = request.POST.get('t2', False)
        btype = request.POST.get('t3', False)
        expiry = request.POST.get('t4', False)
        dd = str(date.today())
        db_connection = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'lifelink',charset='utf8')
        db_cursor = db_connection.cursor()
        student_sql_query = "INSERT INTO donation VALUES('"+username+"','"+donor+"','"+volume+"','"+btype+"','"+dd+"','"+expiry+"')"
        db_cursor.execute(student_sql_query)
        db_connection.commit()
        updateQuantity(username, btype, volume)
        output = "Blood donation successfully updated in Database"
        context= {'data':output}
        return render(request, 'BankScreen.html', context)

def DonationDrive(request):
    if request.method == 'GET':
        output = '<tr><td><font size="3" color="black">Choose&nbsp;Donor</td><td><select name="t1">'
        con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'lifelink',charset='utf8')
        with con:
            cur = con.cursor()
            cur.execute("select username FROM register where usertype='Donor'")
            rows = cur.fetchall()
            for row in rows:
                output += '<option value="'+row[0]+'">'+row[0]+'</option>'
        output += '</select></td></tr>'        
        context= {'data1':output}
        return render(request, 'DonationDrive.html', context)

def RegisterAction(request):
    if request.method == 'POST':
        global username
        username = request.POST.get('t1', False)
        password = request.POST.get('t2', False)
        contact = request.POST.get('t3', False)
        email = request.POST.get('t4', False)
        address = request.POST.get('t5', False)
        area = request.POST.get('t6', False)
        desc = request.POST.get('t7', False)
        utype = request.POST.get('t8', False)
        
        output = "none"
        con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'lifelink',charset='utf8')
        with con:
            cur = con.cursor()
            cur.execute("select username FROM register")
            rows = cur.fetchall()
            for row in rows:
                if row[0] == username:
                    output = username+" Username already exists"
                    break                
        if output == "none":
            db_connection = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'lifelink',charset='utf8')
            db_cursor = db_connection.cursor()
            student_sql_query = "INSERT INTO register VALUES('"+username+"','"+password+"','"+contact+"','"+email+"','"+address+"','"+area+"','"+desc+"','"+utype+"')"
            db_cursor.execute(student_sql_query)
            db_connection.commit()
            print(db_cursor.rowcount, "Record Inserted")
            if db_cursor.rowcount == 1:
                output = "Signup process completed. Login to perform Blood Donation Activities"
        context= {'data':output}
        return render(request, 'Register.html', context)

def checkUser(user, password):
    global username, usertype
    status = "none"
    usertype = ""
    con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'lifelink',charset='utf8')
    with con:
        cur = con.cursor()
        cur.execute("select username,password,usertype FROM register")
        rows = cur.fetchall()
        for row in rows:
            if row[0] == user and row[1] == password:
                usertype = row[2]
                username = user
                status = "success"
                break
    return status, usertype

def HospitalLoginAction(request):
    global username
    if request.method == 'POST':
        global username, usertype            
        users = request.POST.get('t1', False)
        password = request.POST.get('t2', False)
        status, usertype = checkUser(users, password)
        print(status+" "+usertype)
        if status == 'success' and usertype == "Hospital":
            context= {'data':'Welcome '+username}
            return render(request, "HospitalScreen.html", context)
        else:
            context= {'data':'Invalid username'}
            return render(request, 'HospitalLogin.html', context)

def PatientLoginAction(request):
    global username
    if request.method == 'POST':
        global username, usertype            
        users = request.POST.get('t1', False)
        password = request.POST.get('t2', False)
        status, usertype = checkUser(users, password)
        if status == 'success' and usertype == "Patient":
            context= {'data':'Welcome '+username}
            return render(request, "PatientScreen.html", context)
        else:
            context= {'data':'Invalid username'}
            return render(request, 'PatientLogin.html', context)          

def DonorLoginAction(request):
    global username
    if request.method == 'POST':
        global username, usertype            
        users = request.POST.get('t1', False)
        password = request.POST.get('t2', False)
        status, usertype = checkUser(users, password)
        if status == 'success' and usertype == "Donor":
            context= {'data':'Welcome '+username}
            return render(request, "DonorScreen.html", context)
        else:
            context= {'data':'Invalid username'}
            return render(request, 'DonorLogin.html', context)        

def BankLoginAction(request):
    global username
    if request.method == 'POST':
        global username, usertype            
        users = request.POST.get('t1', False)
        password = request.POST.get('t2', False)
        status, usertype = checkUser(users, password)
        if status == 'success' and usertype == "Blood Bank":
            context= {'data':'Welcome '+username}
            return render(request, "BankScreen.html", context)
        else:
            context= {'data':'Invalid username'}
            return render(request, 'BankLogin.html', context)        

def DonorLogin(request):
    if request.method == 'GET':
       return render(request, 'DonorLogin.html', {})

def PatientLogin(request):
    if request.method == 'GET':
       return render(request, 'PatientLogin.html', {})    

def HospitalLogin(request):
    if request.method == 'GET':
       return render(request, 'HospitalLogin.html', {})

def BankLogin(request):
    if request.method == 'GET':
       return render(request, 'BankLogin.html', {})    

def index(request):
    if request.method == 'GET':
        global r2_score, rmse, mae
        output='<table border=1 align=center width=100%><tr><th><font size="3" color="black">ML Algorithm Name</th><th><font size="3" color="black">R2 Score</th>'
        output += '<th><font size="3" color="black">Root Mean Square Error</th><th><font size="3" color="black">Mean Square Error</th></tr>'
        output += '<td><font size="3" color="black">Random Forest</td><td><font size="3" color="black">'+str(round(r2_score,2))+'</td><td><font size="3" color="black">'+str(round(rmse,2))+'</td>'
        output += '<td><font size="3" color="black">'+str(round(mae,2))+'</td></tr>'
        output+= "</table></br>"
        plt.figure(figsize=(4, 3))
        values = [rmse, mae]
        metrics = ['RMSE', 'MAE']
        sns.barplot(x=metrics, y=values)
        plt.title("Random Forest ML Performance Graph")
        plt.xlabel('Metrics')
        plt.ylabel('Error Rate')
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        img_b64 = base64.b64encode(buf.getvalue()).decode()
        plt.clf()
        plt.cla()
        context= {'data':"Random Forest Blood Demand Forecasting Performance<br/><br/>"+output, 'img': img_b64}
        return render(request, 'index.html', context)

def Register(request):
    if request.method == 'GET':
       return render(request, 'Register.html', {})




    

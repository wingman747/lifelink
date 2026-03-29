from django.shortcuts import render, redirect
from django.template import RequestContext
from django.contrib import messages
from django.http import HttpResponse
from django.conf import settings
from django.db import models, transaction
from django.utils import timezone
from django.contrib.auth.models import User
from .models import HospitalBloodBankVerification, InstitutionUser
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
from datetime import timedelta
import smtplib

global username, dataset, label_encoder, rf, scaler, usertype, admin_username

dataset = pd.read_csv("Dataset/Blood.csv")
label_encoder = []
columns = dataset.columns
types = dataset.dtypes.values
for j in range(len(types)):
    name = types[j]
    if name == 'object':
        le = LabelEncoder()
        dataset[columns[j]] = pd.Series(le.fit_transform(dataset[columns[j]].astype(str)))
        label_encoder.append([columns[j], le])
dataset.fillna(dataset.mean(), inplace = True)

Y = dataset['demand_units'].ravel()
dataset.drop(['demand_units'], axis = 1,inplace=True)
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

# ============= HELPER FUNCTIONS =============

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

def sendEmail(em, btype, plate):
    msg = "Urgent required "+btype+" Blood with number of platelets as "+plate
    print(em)
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as connection:
        email_address = 'kaleem202120@gmail.com'
        email_password = 'xyljzncebdxcubjq'
        connection.login(email_address, email_password)
        connection.sendmail(from_addr="kaleem202120@gmail.com", to_addrs=em, msg="Subject : Alert from LIFELINK\n"+msg)

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

# ============= PUBLIC VIEWS =============

def index(request):
    if request.method == 'GET':
        global r2_score, rmse, mae
        
        output='<table border=1 align=center width=100%><tr><th><font size="3" color="black">ML Algorithm Name</th><th><font size="3" color="black">R2 Score</th>'
        output += '<th><font size="3" color="black">Root Mean Square Error</th><th><font size="3" color="black">Mean Square Error</th></tr>'
        output += '<td><font size="3" color="black">Random Forest</td><td><font size="3" color="black">'+str(round(r2_score,2))+'</td><td><font size="3" color="black">'+str(round(rmse,2))+'</td>'
        output += '<td><font size="3" color="black">'+str(round(mae,2))+'</td></tr>'
        output+= "</table></br>"
        
        total_users = 0
        total_donors = 0
        total_hospitals = 0
        total_blood_banks = 0
        total_donations = 0
        blood_type_distribution = {}
        
        try:
            con = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='root', database='lifelink', charset='utf8')
            with con:
                cur = con.cursor()
                
                cur.execute("select count(*) FROM register")
                total_users = cur.fetchone()[0]
                
                cur.execute("select count(*) FROM register where usertype='Donor'")
                total_donors = cur.fetchone()[0]
                
                cur.execute("select count(*) FROM register where usertype='Hospital'")
                total_hospitals = cur.fetchone()[0]
                
                cur.execute("select count(*) FROM register where usertype='Blood Bank'")
                total_blood_banks = cur.fetchone()[0]
                
                cur.execute("select count(*) FROM donation")
                total_donations = cur.fetchone()[0]
                
                cur.execute("select blood_type, sum(quantity) FROM inventory group by blood_type")
                rows = cur.fetchall()
                for row in rows:
                    blood_type_distribution[row[0]] = row[1]
        except:
            pass
        
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
        
        context = {
            'data': "Random Forest Blood Demand Forecasting Performance<br/><br/>"+output, 
            'img': img_b64,
            'total_users': total_users,
            'total_donors': total_donors,
            'total_hospitals': total_hospitals,
            'total_blood_banks': total_blood_banks,
            'total_donations': total_donations,
            'blood_type_distribution': blood_type_distribution
        }
        return render(request, 'index.html', context)

def Register(request):
    """Registration form with location"""
    if request.method == 'GET':
        return render(request, 'register_with_location.html', {})


def RegisterAction(request):
    """Handle registration"""
    if request.method == 'POST':
        username = request.POST.get('t1', '')
        password = request.POST.get('t2', '')
        phone = request.POST.get('t3', '')
        email = request.POST.get('t4', '')
        address = request.POST.get('t5', '')
        location = request.POST.get('t6', '')
        description = request.POST.get('t7', '')
        user_type = request.POST.get('t8', '')
        latitude = request.POST.get('latitude', '')
        longitude = request.POST.get('longitude', '')
        
        try:
            con = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='root', database='lifelink', charset='utf8')
            with con:
                cur = con.cursor()
                
                # Check if user already exists
                cur.execute("SELECT * FROM user WHERE username=%s", (username,))
                if cur.fetchone():
                    data = "Username already exists!"
                    context = {'data': data}
                    return render(request, 'register_with_location.html', context)
                
                # Insert user
                query = "INSERT INTO user (username, password, phone, email, address, location, description, user_type) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                cur.execute(query, (username, password, phone, email, address, location, description, user_type))
                
                # If Blood Bank or Hospital, also insert location data
                if user_type == 'Blood Bank' and latitude and longitude:
                    query2 = "INSERT INTO blood_bank (bank_name, latitude, longitude, address, phone, email, city) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                    cur.execute(query2, (username, float(latitude), float(longitude), address, phone, email, location))
                
                elif user_type == 'Hospital' and latitude and longitude:
                    query3 = "INSERT INTO hospitals (hospital_name, latitude, longitude, address, phone, email, city) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                    cur.execute(query3, (username, float(latitude), float(longitude), address, phone, email, location))
                
                con.commit()
                data = f'✓ {user_type} registered successfully! You can now login.'
        except Exception as e:
            data = f'Error: {str(e)}'
        
        context = {'data': data}
        return render(request, 'register_with_location.html', context)

def HospitalLogin(request):
    if request.method == 'GET':
       return render(request, 'HospitalLogin.html', {})

def HospitalLoginAction(request):
    global username
    if request.method == 'POST':
        global username, usertype            
        users = request.POST.get('t1', False)
        password = request.POST.get('t2', False)
        status, usertype = checkUser(users, password)
        if status == 'success' and usertype == "Hospital":
            return redirect('/HospitalDashboard/')
        else:
            context= {'data':'Invalid username'}
            return render(request, 'HospitalLogin.html', context)
def SearchBlood(request):
    if request.method == 'GET':
       return render(request, 'SearchBlood.html', {})

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

def PatientLogin(request):
    if request.method == 'GET':
       return render(request, 'PatientLogin.html', {})

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

def PatientSearch(request):
    if request.method == 'GET':
       return render(request, 'PatientSearch.html', {})

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

def DonorLogin(request):
    if request.method == 'GET':
       return render(request, 'DonorLogin.html', {})

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

def BankLogin(request):
    if request.method == 'GET':
       return render(request, 'BankLogin.html', {})

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

def ReleaseBlood(request):
    """Release blood to hospital form"""
    if request.method == 'GET':
        hospitals = []
        try:
            con = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='root', database='lifelink', charset='utf8')
            with con:
                cur = con.cursor()
                cur.execute("SELECT DISTINCT hospital_name FROM blood_request WHERE status='Pending' ORDER BY hospital_name")
                hospitals = [row[0] for row in cur.fetchall()]
        except Exception as e:
            hospitals = []
        
        context = {'hospitals': hospitals}
        return render(request, 'ReleaseBlood.html', context)


def ReleaseBloodAction(request):
    """Process blood release"""
    if request.method == 'POST':
        global username
        hospital_name = request.POST.get('t1', '')
        blood_type = request.POST.get('t2', '')
        quantity = request.POST.get('t3', '')
        dd = str(date.today())
        expiry_date = str(date.today() + timedelta(days=42))  # Blood typically lasts 42 days
        
        try:
            con = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='root', database='lifelink', charset='utf8')
            with con:
                cur = con.cursor()
                
                # Add to hospital inventory
                query = "INSERT INTO hospital_inventory (hospital_name, blood_type, quantity, received_date, expiry_date) VALUES (%s, %s, %s, %s, %s)"
                cur.execute(query, (hospital_name, blood_type, float(quantity), dd, expiry_date))
                
                # Update blood request status
                query2 = "UPDATE blood_request SET status='Approved' WHERE hospital_name=%s AND blood_type=%s AND status='Pending' LIMIT 1"
                cur.execute(query2, (hospital_name, blood_type))
                
                con.commit()
                message = f'✓ Released {quantity}L of {blood_type} blood to {hospital_name} successfully!'
        except Exception as e:
            message = f'Error: {str(e)}'
        
        hospitals = []
        try:
            con = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='root', database='lifelink', charset='utf8')
            with con:
                cur = con.cursor()
                cur.execute("SELECT DISTINCT hospital_name FROM blood_request WHERE status='Pending' ORDER BY hospital_name")
                hospitals = [row[0] for row in cur.fetchall()]
        except:
            hospitals = []
        
        context = {'message': message, 'hospitals': hospitals}
        return render(request, 'ReleaseBlood.html', context)

def ViewInventory(request):
    if request.method == 'GET':
        global username
        output='<table border=1 align=center width=100%><tr><th><font size="3" color="black">Blood Type</th><th><font size="3" color="black">Available Quantity</th>'
        output += '<th><font size="3" color="black">Status</th><th><font size="3" color="black">Action</th></tr>'
        con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'lifelink',charset='utf8')
        with con:
            cur = con.cursor()
            cur.execute("select * from inventory where username='"+username+"'")
            rows = cur.fetchall()
            for row in rows:
                quantity = row[2]
                if quantity < 5:
                    status = '<font size="3" color="red">⚠️ LOW STOCK</font>'
                elif quantity < 10:
                    status = '<font size="3" color="orange">⚡ MEDIUM</font>'
                else:
                    status = '<font size="3" color="green">✅ GOOD</font>'
                output += '<td><font size="3" color="black">'+row[1]+'</td><td><font size="3" color="black">'+str(row[2])+'</td><td>'+status+'</td>'
                output += '<td><a href="/UpdateInventoryForm/?btype='+row[1]+'">Edit</a></td></tr>'
        output+= "</table></br></br></br></br>"
        context= {'data':output}
        return render(request, 'BankScreen.html', context)

def UpdateInventoryForm(request):
    if request.method == 'GET':
        btype = request.GET.get('btype', False)
        output = '<tr><td><font size="3" color="black">Blood&nbsp;Type</td><td><input type="text" name="t1" value="'+btype+'" readonly></td></tr>'
        output += '<tr><td><font size="3" color="black">Add&nbsp;Quantity</td><td><input type="number" name="t2" placeholder="Enter quantity to add" step="0.1"></td></tr>'
        context= {'data1':output, 'btype': btype}
        return render(request, 'UpdateInventory.html', context)

def UpdateInventoryAction(request):
    if request.method == 'POST':
        global username
        btype = request.POST.get('t1', False)
        quantity = request.POST.get('t2', False)
        quantity = float(quantity)
        db_connection = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'lifelink',charset='utf8')
        db_cursor = db_connection.cursor()
        student_sql_query = "update inventory set quantity=quantity+"+str(quantity)+" where username='"+username+"' and blood_type='"+btype+"'"
        db_cursor.execute(student_sql_query)
        db_connection.commit()
        output = "Inventory updated successfully"
        context= {'data':output}
        return render(request, 'BankScreen.html', context)

def BloodExpiryTracker(request):
    if request.method == 'GET':
        global username
        output='<table border=1 align=center width=100%><tr><th><font size="3" color="black">Donor Name</th><th><font size="3" color="black">Blood Type</th>'
        output += '<th><font size="3" color="black">Donation Date</th><th><font size="3" color="black">Expiry Date</th><th><font size="3" color="black">Days Left</th><th><font size="3" color="black">Status</th></tr>'
        con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'lifelink',charset='utf8')
        with con:
            cur = con.cursor()
            cur.execute("select * from donation where username='"+username+"'")
            rows = cur.fetchall()
            for row in rows:
                expiry_date = row[5]
                donation_date = row[4]
                date1 = datetime.strptime(expiry_date, "%Y-%m-%d")
                date2 = datetime.strptime(str(date.today()), "%Y-%m-%d")
                delta = date1 - date2
                days_left = delta.days
                if days_left < 0:
                    status = '<font size="3" color="red">   EXPIRED</font>'
                elif days_left < 7:
                    status = '<font size="3" color="orange">⚠️ EXPIRING SOON</font>'
                else:
                    status = '<font size="3" color="green">✅ VALID</font>'
                output += '<td><font size="3" color="black">'+row[1]+'</td><td><font size="3" color="black">'+row[3]+'</td><td><font size="3" color="black">'+donation_date+'</td>'
                output += '<td><font size="3" color="black">'+expiry_date+'</td><td><font size="3" color="black">'+str(days_left)+'</td><td>'+status+'</td></tr>'
        output+= "</table></br></br></br></br>"
        context= {'data':output}
        return render(request, 'BankScreen.html', context)

def Forecast(request):
    if request.method == 'GET':
       return render(request, 'Forecast.html', {})

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
        for i in range(len(label_encoder)):
            le = label_encoder[i]
            data[le[0]] = pd.Series(le[1].transform(data[le[0]].astype(str)))
        data = data.values 
        data = scaler.transform(data)
        predict = rf.predict(data).ravel()[0]
        output = "<font size=4 color=blue>Forecasted Demand Based on Selected Input = "+str(round(predict,2))+" Ltrs</font>"
        context= {'data':output}
        return render(request, 'BankScreen.html', context)

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

# ============= ADMIN FUNCTIONS =============

def AdminLogin(request):
    if request.method == 'GET':
        return render(request, 'AdminLogin.html', {})

def AdminLoginAction(request):
    if request.method == 'POST':
        global admin_username
        uname = request.POST.get('t1', False)
        pwd = request.POST.get('t2', False)
        
        admin_user = 'admin'
        admin_pass = 'admin123'
        
        if uname == admin_user and pwd == admin_pass:
            admin_username = uname
            return redirect('/AdminDashboard/')
        else:
            context = {'data': 'Invalid admin credentials!'}
            return render(request, 'AdminLogin.html', context)

def AdminDashboard(request):
    if request.method == 'GET':
        output = '<div style="padding: 20px;">'
        output += '<h2>📊 Admin Dashboard</h2>'
        
        try:
            con = pymysql.connect(
                host='127.0.0.1',
                port=3306,
                user='root',
                password='root',
                database='lifelink',
                charset='utf8'
            )
            with con:
                cur = con.cursor()
                cur.execute("SELECT COUNT(*) FROM register")
                total_register_users = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM register WHERE usertype='Donor'")
                total_donors = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM register WHERE usertype='Hospital'")
                total_hospitals = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM register WHERE usertype='Blood Bank'")
                total_blood_banks = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM register WHERE usertype='Patient'")
                total_patients = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM donation")
                total_donations = cur.fetchone()[0]
            
            total_django_users = User.objects.count()
            total_institutions = HospitalBloodBankVerification.objects.count()
            verified_institutions = HospitalBloodBankVerification.objects.filter(is_verified=True).count()
            pending_institutions = total_institutions - verified_institutions
            institution_users = InstitutionUser.objects.count()
            
            output += '<div style="display: flex; gap: 20px; flex-wrap: wrap;">'
            output += '<div style="border: 2px solid #3498db; padding: 20px; width: 200px; text-align: center; border-radius: 8px;">'
            output += '<h3 style="color: #3498db;">👤 Users</h3>'
            output += '<h1 style="color: #3498db;">' + str(total_register_users) + '</h1>'
            output += '</div>'
            output += '<div style="border: 2px solid #e74c3c; padding: 20px; width: 200px; text-align: center; border-radius: 8px;">'
            output += '<h3 style="color: #e74c3c;">🩸 Donors</h3>'
            output += '<h1 style="color: #e74c3c;">' + str(total_donors) + '</h1>'
            output += '</div>'
            output += '<div style="border: 2px solid #2ecc71; padding: 20px; width: 200px; text-align: center; border-radius: 8px;">'
            output += '<h3 style="color: #2ecc71;">🏥 Hospitals</h3>'
            output += '<h1 style="color: #2ecc71;">' + str(total_hospitals) + '</h1>'
            output += '</div>'
            output += '<div style="border: 2px solid #f39c12; padding: 20px; width: 200px; text-align: center; border-radius: 8px;">'
            output += '<h3 style="color: #f39c12;">🏦 Banks</h3>'
            output += '<h1 style="color: #f39c12;">' + str(total_blood_banks) + '</h1>'
            output += '</div>'
            output += '<div style="border: 2px solid #9b59b6; padding: 20px; width: 200px; text-align: center; border-radius: 8px;">'
            output += '<h3 style="color: #9b59b6;">🏢 Institutions</h3>'
            output += '<h1 style="color: #9b59b6;">' + str(total_institutions) + '</h1>'
            output += '<p style="color: green;">✓ ' + str(verified_institutions) + '</p>'
            output += '</div>'
            output += '<div style="border: 2px solid #c0392b; padding: 20px; width: 200px; text-align: center; border-radius: 8px;">'
            output += '<h3 style="color: #c0392b;">📋 Donations</h3>'
            output += '<h1 style="color: #c0392b;">' + str(total_donations) + '</h1>'
            output += '</div>'
            output += '</div><hr style="margin-top: 40px;">'
            output += '<h3>Quick Links</h3>'
            output += '<a href="/admin/">Go to Django Admin Panel</a>'
            
        except Exception as e:
            output += '<div style="color: red;">Error: ' + str(e) + '</div>'
        
        output += '</div>'
        context = {'data': output}
        return render(request, 'AdminDashboard.html', context)

def AdminViewUsers(request):
    if request.method == 'GET':
        output = '<table border=1 align=center width=100%>'
        output += '<tr><th>Username</th><th>Contact</th><th>Email</th><th>User Type</th></tr>'
        
        try:
            con = pymysql.connect(
                host='127.0.0.1',
                port=3306,
                user='root',
                password='root',
                database='lifelink',
                charset='utf8'
            )
            cur = con.cursor()
            cur.execute("SELECT username, contact, email, usertype FROM register")
            rows = cur.fetchall()
            con.close()
            
            if rows:
                for row in rows:
                    output += '<tr>'
                    output += '<td>' + str(row[0]) + '</td>'
                    output += '<td>' + str(row[1]) + '</td>'
                    output += '<td>' + str(row[2]) + '</td>'
                    output += '<td>' + str(row[3]) + '</td>'
                    output += '</tr>'
            else:
                output += '<tr><td colspan="4">No users found</td></tr>'
                
        except pymysql.Error as e:
            output += '<tr><td colspan="4">Database Error: ' + str(e) + '</td></tr>'
        except Exception as e:
            output += '<tr><td colspan="4">Error: ' + str(e) + '</td></tr>'
        
        output += '</table>'
        return render(request, 'AdminViewUsers.html', {'data': output})


def AdminDeleteUser(request):
    if request.method == 'GET':
        username = request.GET.get('username', False)
        try:
            con = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='root', database='lifelink', charset='utf8')
            with con:
                cur = con.cursor()
                cur.execute("DELETE FROM register WHERE username=%s", (username,))
                con.commit()
                message = 'User deleted successfully!'
        except Exception as e:
            message = 'Error deleting user: ' + str(e)
        
        context = {'data': message}
        return render(request, 'AdminViewUsers.html', context)

def AdminViewDonations(request):
    if request.method == 'GET':
        output = '<table border=1 align=center width=100%><tr><th><font size="3">Donor</th><th><font size="3">Blood Type</th><th><font size="3">Quantity</th><th><font size="3">Blood Bank</th><th><font size="3">Donation Date</th><th><font size="3">Expiry Date</th></tr>'
        
        try:
            con = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='root', database='lifelink', charset='utf8')
            with con:
                cur = con.cursor()
                # Changed: removed ORDER BY id DESC since donation table might not have id column
                cur.execute("select donor_name, blood_type, volume_donate, username, donate_date, expiry_days from donation")
                rows = cur.fetchall()
                for row in rows:
                    output += '<tr><td><font size="3">'+str(row[0])+'</td><td><font size="3">'+str(row[1])+'</td><td><font size="3">'+str(row[2])+'</td><td><font size="3">'+str(row[3])+'</td><td><font size="3">'+str(row[4])+'</td><td><font size="3">'+str(row[5])+'</td></tr>'
        except Exception as e:
            output += '<tr><td colspan="6"><font size="3" color="red">Error: ' + str(e) + '</td></tr>'
        
        output += "</table></br></br></br>"
        context = {'data': output}
        return render(request, 'AdminViewDonations.html', context)

def AdminViewBloodBanks(request):
    if request.method == 'GET':
        output = '<table border=1 align=center width=100%><tr><th><font size="3">Bank Name</th><th><font size="3">Contact</th><th><font size="3">Email</th><th><font size="3">Area</th></tr>'
        
        try:
            con = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='root', database='lifelink', charset='utf8')
            with con:
                cur = con.cursor()
                cur.execute("SELECT username, contact, email, area_location FROM register WHERE usertype='Blood Bank'")
                rows = cur.fetchall()
                for row in rows:
                    output += '<tr><td><font size="3">'+str(row[0])+'</td><td><font size="3">'+str(row[1])+'</td><td><font size="3">'+str(row[2])+'</td><td><font size="3">'+str(row[3])+'</td></tr>'
        except Exception as e:
            output += '<tr><td colspan="4"><font size="3" color="red">Error: ' + str(e) + '</td></tr>'
        
        output += "</table></br></br></br>"
        context = {'data': output}
        return render(request, 'AdminViewBloodBanks.html', context)

def AdminSystemReports(request):
    if request.method == 'GET':
        try:
            con = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='root', database='lifelink', charset='utf8')
            with con:
                cur = con.cursor()
                
                cur.execute("select blood_type, count(*) from donation group by blood_type")
                blood_stats = cur.fetchall()
                
                blood_output = '<h3>Blood Type Statistics</h3>'
                blood_output += '<table border=1 align=center width=50%><tr><th>Blood Type</th><th>Count</th></tr>'
                for row in blood_stats:
                    blood_output += '<tr><td>'+row[0]+'</td><td>'+str(row[1])+'</td></tr>'
                blood_output += '</table><br/><br/>'
                
                cur.execute("select usertype, count(*) from register group by usertype")
                user_stats = cur.fetchall()
                
                user_output = '<h3>User Type Statistics</h3>'
                user_output += '<table border=1 align=center width=50%><tr><th>Type</th><th>Count</th></tr>'
                for row in user_stats:
                    user_output += '<tr><td>'+row[0]+'</td><td>'+str(row[1])+'</td></tr>'
                user_output += '</table><br/><br/>'
                
                context = {'data': blood_output + user_output}
                return render(request, 'AdminSystemReports.html', context)
        except Exception as e:
            context = {'data': '<font color="red">Error: ' + str(e) + '</font>'}
            return render(request, 'AdminSystemReports.html', context)

def AdminActivityLog(request):
    if request.method == 'GET':
        output = '<table border=1 align=center width=100%><tr><th><font size="3">Username</th><th><font size="3">Type</th><th><font size="3">Contact</th></tr>'
        
        try:
            con = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='root', database='lifelink', charset='utf8')
            with con:
                cur = con.cursor()
                # Removed ORDER BY id DESC - use direct query without ordering or order by a column that exists
                cur.execute("select username, usertype, contact from register limit 100")
                rows = cur.fetchall()
                for row in rows:
                    output += '<tr><td><font size="3">'+str(row[0])+'</td><td><font size="3">'+str(row[1])+'</td><td><font size="3">'+str(row[2])+'</td></tr>'
        except Exception as e:
            output += '<tr><td colspan="3"><font size="3" color="red">Error: ' + str(e) + '</td></tr>'
        
        output += "</table></br></br></br>"
        context = {'data': output}
        return render(request, 'AdminActivityLog.html', context)

def AdminLogout(request):
    global admin_username
    admin_username = None
    return redirect('index')

def register_institution_user(request):
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')
        institution_id = request.POST.get('institution', '')
        designation = request.POST.get('designation', '')
        
        if password != password_confirm:
            messages.error(request, "Passwords don't match")
            verified_institutions = HospitalBloodBankVerification.objects.filter(is_verified=True)
            context = {'institutions': verified_institutions}
            return render(request, 'institution_register.html', context)
        
        try:
            institution = HospitalBloodBankVerification.objects.get(id=institution_id)
            if not institution.is_verified:
                messages.error(request, "Your institution has not been verified yet. Please contact admin.")
                verified_institutions = HospitalBloodBankVerification.objects.filter(is_verified=True)
                context = {'institutions': verified_institutions}
                return render(request, 'institution_register.html', context)
        except HospitalBloodBankVerification.DoesNotExist:
            messages.error(request, "Invalid institution selected")
            verified_institutions = HospitalBloodBankVerification.objects.filter(is_verified=True)
            context = {'institutions': verified_institutions}
            return render(request, 'institution_register.html', context)
        
        if User.objects.filter(username=username).exists():
            messages.error(request, f"Username '{username}' already exists")
            verified_institutions = HospitalBloodBankVerification.objects.filter(is_verified=True)
            context = {'institutions': verified_institutions}
            return render(request, 'institution_register.html', context)
        
        try:
            with transaction.atomic():
                user = User.objects.create_user(username=username, password=password)
                institution_user = InstitutionUser.objects.create(
                    username=user,
                    institution=institution,
                    designation=designation
                )
                messages.success(request, "Registration successful! You can now login.")
                return redirect('HospitalLogin')
        except Exception as e:
            messages.error(request, f"Registration failed: {str(e)}")
            verified_institutions = HospitalBloodBankVerification.objects.filter(is_verified=True)
            context = {'institutions': verified_institutions}
            return render(request, 'institution_register.html', context)
    
    verified_institutions = HospitalBloodBankVerification.objects.filter(is_verified=True)
    context = {'institutions': verified_institutions}
    return render(request, 'institution_register.html', context)

def institution_not_verified(request):
    return render(request, 'institution_not_verified.html', {})

def account_disabled(request):
    return render(request, 'account_disabled.html', {})

def AdminViewInstitutions(request):
    if request.method == 'GET':
        output = '<table border=1 align=center width=100%><tr>'
        output += '<th><font size="3" color="black">ID</th>'
        output += '<th><font size="3" color="black">Name</th>'
        output += '<th><font size="3" color="black">Type</th>'
        output += '<th><font size="3" color="black">Registration #</th>'
        output += '<th><font size="3" color="black">Email</th>'
        output += '<th><font size="3" color="black">Status</th>'
        output += '<th><font size="3" color="black">Action</th>'
        output += '</tr>'
        
        try:
            institutions = HospitalBloodBankVerification.objects.all().order_by('-id')
            
            if institutions.exists():
                for inst in institutions:
                    status_color = 'green' if inst.is_verified else 'red'
                    status_text = '✓ Verified' if inst.is_verified else '✗ Pending'
                    
                    output += '<tr>'
                    output += '<td><font size="3" color="black">' + str(inst.id) + '</font></td>'
                    output += '<td><font size="3" color="black">' + inst.name + '</font></td>'
                    output += '<td><font size="3" color="black">' + inst.get_institution_type_display() + '</font></td>'
                    output += '<td><font size="3" color="black">' + inst.registration_number + '</font></td>'
                    output += '<td><font size="3" color="black">' + inst.email + '</font></td>'
                    output += '<td><font size="3" color="' + status_color + '">' + status_text + '</font></td>'
                    output += '<td><a href="/admin/bloodapp/hospitalbloodbankverification/' + str(inst.id) + '/change/">Edit</a></td>'
                    output += '</tr>'
            else:
                output += '<tr><td colspan="7"><font size="3" color="red">No institutions registered</font></td></tr>'
        except Exception as e:
            output += '<tr><td colspan="7"><font size="3" color="red">Error: ' + str(e) + '</font></td></tr>'
        
        output += '</table><br/>'
        context = {'data': output}
        return render(request, 'AdminViewInstitutions.html', context)

def AdminViewInstitutionUsers(request):
    if request.method == 'GET':
        output = '<table border=1 align=center width=100%><tr>'
        output += '<th><font size="3" color="black">User ID</th>'
        output += '<th><font size="3" color="black">Username</th>'
        output += '<th><font size="3" color="black">Institution</th>'
        output += '<th><font size="3" color="black">Designation</th>'
        output += '<th><font size="3" color="black">Status</th>'
        output += '<th><font size="3" color="black">Joined</th>'
        output += '</tr>'
        
        try:
            inst_users = InstitutionUser.objects.select_related('username', 'institution').all().order_by('-id')
            
            if inst_users.exists():
                for iu in inst_users:
                    status_color = 'green' if iu.is_active else 'red'
                    status_text = '🟢 Active' if iu.is_active else '🔴 Inactive'
                    
                    output += '<tr>'
                    output += '<td><font size="3" color="black">' + str(iu.username.id) + '</font></td>'
                    output += '<td><font size="3" color="black">' + iu.username.username + '</font></td>'
                    output += '<td><font size="3" color="black">' + iu.institution.name + '</font></td>'
                    output += '<td><font size="3" color="black">' + iu.designation + '</font></td>'
                    output += '<td><font size="3" color="' + status_color + '">' + status_text + '</font></td>'
                    output += '<td><font size="3" color="black">' + iu.created_at.strftime('%Y-%m-%d') + '</font></td>'
                    output += '</tr>'
            else:
                output += '<tr><td colspan="6"><font size="3" color="red">No institution users found</font></td></tr>'
        except Exception as e:
            output += '<tr><td colspan="6"><font size="3" color="red">Error: ' + str(e) + '</font></td></tr>'
        
        output += '</table><br/>'
        context = {'data': output}
        return render(request, 'AdminViewInstitutionUsers.html', context)


# ============= HOSPITAL ENHANCEMENTS =============

def HospitalDashboard(request):
    """Hospital dashboard with statistics"""
    if request.method == 'GET':
        global username
        output = ''
        
        try:
            con = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='root', database='lifelink', charset='utf8')
            with con:
                cur = con.cursor()
                
                cur.execute("SELECT COUNT(*) FROM blood_request WHERE hospital_name=%s AND status='Pending'", (username,))
                pending_requests = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM hospital_patients WHERE hospital_name=%s", (username,))
                total_patients = cur.fetchone()[0]
                
                cur.execute("SELECT SUM(quantity) FROM hospital_inventory WHERE hospital_name=%s", (username,))
                result = cur.fetchone()[0]
                total_inventory = result if result else 0
        except Exception as e:
            pending_requests = 0
            total_patients = 0
            total_inventory = 0
        
        output += '<center><h2>Welcome ' + username + '</h2></center><br/>'
        output += '<table border=1 align=center width=80%>'
        output += '<tr><th><font size="4" color="black">Pending Requests</font></th><th><font size="4" color="black">Total Patients</font></th><th><font size="4" color="black">Blood Inventory</font></th></tr>'
        output += '<tr>'
        output += '<td align=center><font size="5" color="red"><b>' + str(pending_requests) + '</b></font></td>'
        output += '<td align=center><font size="5" color="blue"><b>' + str(total_patients) + '</b></font></td>'
        output += '<td align=center><font size="5" color="green"><b>' + str(total_inventory) + 'L</b></font></td>'
        output += '</tr>'
        output += '</table><br/><br/>'
        
        output += '<center>'
        output += '<a href="{% url \'RequestBlood\' %}"><font size="3" color="blue">Request Blood</font></a> | '
        output += '<a href="{% url \'AddPatient\' %}"><font size="3" color="blue">Add Patient</font></a> | '
        output += '<a href="{% url \'ViewPatients\' %}"><font size="3" color="blue">View Patients</font></a> | '
        output += '<a href="{% url \'ViewBloodRequests\' %}"><font size="3" color="blue">View Requests</font></a> | '
        output += '<a href="{% url \'ViewHospitalInventory\' %}"><font size="3" color="blue">View Inventory</font></a> | '
        output += '<a href="{% url \'SearchBlood\' %}"><font size="3" color="blue">Search Blood</font></a>'
        output += '</center>'
        
        context = {'data': output}
        return render(request, 'HospitalScreen.html', context)

def RequestBlood(request):
    """Request blood form"""
    if request.method == 'GET':
        return render(request, 'RequestBlood.html', {})


def RequestBloodAction(request):
    """Process blood request"""
    if request.method == 'POST':
        global username
        btype = request.POST.get('t1', False)
        quantity = request.POST.get('t2', False)
        urgency = request.POST.get('t3', False)
        dd = str(date.today())
        
        try:
            con = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='root', database='lifelink', charset='utf8')
            with con:
                cur = con.cursor()
                query = "INSERT INTO blood_request (hospital_name, blood_type, quantity, urgency, request_date, status) VALUES (%s, %s, %s, %s, %s, %s)"
                cur.execute(query, (username, btype, float(quantity), urgency, dd, 'Pending'))
                con.commit()
                output = 'Blood request for ' + str(quantity) + 'L of ' + btype + ' submitted as ' + urgency
        except Exception as e:
            output = 'Error: ' + str(e)
        
        context = {'data': output}
        return render(request, 'HospitalScreen.html', context)


def ViewBloodRequests(request):
    """View all blood requests made by hospital"""
    if request.method == 'GET':
        global username
        output = '<table border=1 align=center width=100%>'
        output += '<tr><th><font size="3">Request Date</font></th><th><font size="3">Blood Type</font></th><th><font size="3">Quantity</font></th><th><font size="3">Urgency</font></th><th><font size="3">Status</font></th></tr>'
        
        try:
            con = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='root', database='lifelink', charset='utf8')
            with con:
                cur = con.cursor()
                cur.execute("SELECT request_date, blood_type, quantity, urgency, status FROM blood_request WHERE hospital_name=%s ORDER BY request_date DESC", (username,))
                rows = cur.fetchall()
                
                if rows:
                    for row in rows:
                        if row[4] == 'Approved':
                            status_color = 'green'
                        elif row[4] == 'Pending':
                            status_color = 'orange'
                        else:
                            status_color = 'red'
                        
                        output += '<tr>'
                        output += '<td><font size="3">' + str(row[0]) + '</font></td>'
                        output += '<td><font size="3">' + row[1] + '</font></td>'
                        output += '<td><font size="3">' + str(row[2]) + 'L</font></td>'
                        output += '<td><font size="3">' + row[3] + '</font></td>'
                        output += '<td><font size="3" color="' + status_color + '">' + row[4] + '</font></td>'
                        output += '</tr>'
                else:
                    output += '<tr><td colspan="5"><font size="3" color="red">No requests found</font></td></tr>'
        except Exception as e:
            output += '<tr><td colspan="5"><font size="3" color="red">Error: ' + str(e) + '</font></td></tr>'
        
        output += '</table><br/>'
        context = {'data': output}
        return render(request, 'HospitalScreen.html', context)


def AddPatient(request):
    """Add patient record"""
    if request.method == 'GET':
        output = '<tr><td><font size="3" color="black">Patient Name</font></td><td><input type="text" name="t1" required></td></tr>'
        output += '<tr><td><font size="3" color="black">Blood Type Needed</font></td><td><select name="t2" required>'
        blood_types = ['O+', 'O-', 'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-']
        for bt in blood_types:
            output += '<option value="'+bt+'">'+bt+'</option>'
        output += '</select></td></tr>'
        output += '<tr><td><font size="3" color="black">Quantity (Litres)</font></td><td><input type="number" name="t3" step="0.1" min="0.1" required></td></tr>'
        output += '<tr><td><font size="3" color="black">Medical Condition</font></td><td><textarea name="t4" rows="3" cols="30" required></textarea></td></tr>'
        
        from django.middleware.csrf import get_token
        csrf_token = get_token(request)
        output += '<input type="hidden" name="csrfmiddlewaretoken" value="' + csrf_token + '">'
        
        context = {'data1': output}
        return render(request, 'AddPatient.html', context)


def AddPatientAction(request):
    """Save patient record"""
    if request.method == 'POST':
        global username
        patient_name = request.POST.get('t1', False)
        blood_type = request.POST.get('t2', False)
        quantity = request.POST.get('t3', False)
        condition = request.POST.get('t4', False)
        dd = str(date.today())
        
        try:
            con = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='root', database='lifelink', charset='utf8')
            with con:
                cur = con.cursor()
                query = "INSERT INTO hospital_patients (hospital_name, patient_name, blood_type, quantity_needed, medical_condition, admission_date) VALUES (%s, %s, %s, %s, %s, %s)"
                cur.execute(query, (username, patient_name, blood_type, float(quantity), condition, dd))
                con.commit()
                output = 'Patient ' + patient_name + ' added successfully!'
        except Exception as e:
            output = 'Error: ' + str(e)
        
        context = {'data': output}
        return render(request, 'HospitalScreen.html', context)


def ViewPatients(request):
    """View all patients admitted in hospital"""
    if request.method == 'GET':
        global username
        output = '<table border=1 align=center width=100%>'
        output += '<tr><th><font size="3">Patient Name</font></th><th><font size="3">Blood Type</font></th><th><font size="3">Quantity Needed</font></th><th><font size="3">Medical Condition</font></th><th><font size="3">Admission Date</font></th></tr>'
        
        try:
            con = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='root', database='lifelink', charset='utf8')
            with con:
                cur = con.cursor()
                cur.execute("SELECT patient_name, blood_type, quantity_needed, medical_condition, admission_date FROM hospital_patients WHERE hospital_name=%s ORDER BY admission_date DESC", (username,))
                rows = cur.fetchall()
                
                if rows:
                    for row in rows:
                        output += '<tr>'
                        output += '<td><font size="3">' + row[0] + '</font></td>'
                        output += '<td><font size="3">' + row[1] + '</font></td>'
                        output += '<td><font size="3">' + str(row[2]) + 'L</font></td>'
                        output += '<td><font size="3">' + (row[3][:50] + '...' if len(row[3]) > 50 else row[3]) + '</font></td>'
                        output += '<td><font size="3">' + str(row[4]) + '</font></td>'
                        output += '</tr>'
                else:
                    output += '<tr><td colspan="5"><font size="3" color="red">No patients found</font></td></tr>'
        except Exception as e:
            output += '<tr><td colspan="5"><font size="3" color="red">Error: ' + str(e) + '</font></td></tr>'
        
        output += '</table><br/>'
        context = {'data': output}
        return render(request, 'HospitalScreen.html', context)


def ViewHospitalInventory(request):
    """View blood inventory received by hospital"""
    if request.method == 'GET':
        global username
        output = '<table border=1 align=center width=100%>'
        output += '<tr><th><font size="3">Blood Type</font></th><th><font size="3">Quantity</font></th><th><font size="3">Received Date</font></th><th><font size="3">Expiry Date</font></th><th><font size="3">Status</font></th></tr>'
        
        try:
            con = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='root', database='lifelink', charset='utf8')
            with con:
                cur = con.cursor()
                cur.execute("SELECT blood_type, quantity, received_date, expiry_date FROM hospital_inventory WHERE hospital_name=%s", (username,))
                rows = cur.fetchall()
                
                if rows:
                    for row in rows:
                        try:
                            exp_date = datetime.strptime(row[3], "%Y-%m-%d")
                            today = datetime.strptime(str(date.today()), "%Y-%m-%d")
                            days_left = (exp_date - today).days
                            
                            if days_left < 0:
                                status = '<font color="red">EXPIRED</font>'
                            elif days_left < 7:
                                status = '<font color="orange">EXPIRING SOON</font>'
                            else:
                                status = '<font color="green">VALID</font>'
                        except:
                            status = '<font color="gray">-</font>'
                        
                        output += '<tr>'
                        output += '<td><font size="3">' + row[0] + '</font></td>'
                        output += '<td><font size="3">' + str(row[1]) + 'L</font></td>'
                        output += '<td><font size="3">' + str(row[2]) + '</font></td>'
                        output += '<td><font size="3">' + str(row[3]) + '</font></td>'
                        output += '<td>' + status + '</td>'
                        output += '</tr>'
                else:
                    output += '<tr><td colspan="5"><font size="3" color="red">No inventory found</font></td></tr>'
        except Exception as e:
            output += '<tr><td colspan="5"><font size="3" color="red">Error: ' + str(e) + '</font></td></tr>'
        
        output += '</table><br/>'
        context = {'data': output}
        return render(request, 'HospitalScreen.html', context)

def PublicBloodBankMap(request):
    """Public blood bank map view"""
    if request.method == 'GET':
        try:
            con = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='root', database='lifelink', charset='utf8')
            with con:
                cur = con.cursor()
                cur.execute("SELECT bank_name, latitude, longitude, address, phone, city FROM blood_bank WHERE latitude IS NOT NULL AND longitude IS NOT NULL")
                banks = cur.fetchall()
        except:
            banks = []
        
        import folium
        m = folium.Map(location=[20.5937, 78.9629], zoom_start=5, tiles='OpenStreetMap')
        
        for bank in banks:
            bank_name, lat, lon, address, phone, city = bank
            popup_text = f"""
            <b>{bank_name}</b><br>
            📍 {address}<br>
            📱 {phone}<br>
            🏙️ {city}
            """
            
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_text, max_width=300),
                tooltip=bank_name,
                icon=folium.Icon(color='red', icon='droplet', prefix='fa')
            ).add_to(m)
        
        try:
            con = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='root', database='lifelink', charset='utf8')
            with con:
                cur = con.cursor()
                cur.execute("SELECT hospital_name, latitude, longitude, address, phone, city FROM hospitals WHERE latitude IS NOT NULL AND longitude IS NOT NULL")
                hospitals = cur.fetchall()
        except:
            hospitals = []
        
        for hospital in hospitals:
            hosp_name, lat, lon, address, phone, city = hospital
            popup_text = f"""
            <b>{hosp_name}</b><br>
            📍 {address}<br>
            📱 {phone}<br>
            🏙️ {city}
            """
            
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_text, max_width=300),
                tooltip=hosp_name,
                icon=folium.Icon(color='blue', icon='plus', prefix='fa')
            ).add_to(m)
        
        folium.LayerControl().add_to(m)
        map_html = m._repr_html_()
        
        context = {'map': map_html}
        return render(request, 'public_blood_bank_map.html', context)


def PublicFindNearestBloodBank(request):
    """Public find nearest blood bank"""
    if request.method == 'POST':
        user_lat = float(request.POST.get('latitude', 0))
        user_lon = float(request.POST.get('longitude', 0))
        blood_type = request.POST.get('blood_type', '')
        
        try:
            con = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='root', database='lifelink', charset='utf8')
            with con:
                cur = con.cursor()
                cur.execute("""
                    SELECT bb.bank_name, bb.latitude, bb.longitude, bb.address, bb.phone, bb.city
                    FROM blood_bank bb
                    WHERE bb.latitude IS NOT NULL AND bb.longitude IS NOT NULL
                """)
                banks = cur.fetchall()
        except:
            banks = []
        
        from math import radians, cos, sin, asin, sqrt
        
        def haversine(lat1, lon1, lat2, lon2):
            lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            return 6371 * c
        
        nearest_banks = []
        for bank in banks:
            bank_name, lat, lon, address, phone, city = bank
            distance = haversine(user_lat, user_lon, lat, lon)
            nearest_banks.append({
                'name': bank_name,
                'lat': lat,
                'lon': lon,
                'address': address,
                'phone': phone,
                'city': city,
                'distance': round(distance, 2)
            })
        
        nearest_banks.sort(key=lambda x: x['distance'])
        
        import folium
        m = folium.Map(location=[user_lat, user_lon], zoom_start=10, tiles='OpenStreetMap')
        
        folium.Marker(
            location=[user_lat, user_lon],
            popup='Your Location',
            icon=folium.Icon(color='green', icon='user', prefix='fa')
        ).add_to(m)
        
        for bank in nearest_banks[:5]:
            popup_text = f"""
            <b>{bank['name']}</b><br>
            Distance: {bank['distance']} km<br>
            📍 {bank['address']}<br>
            📱 {bank['phone']}
            """
            
            folium.Marker(
                location=[bank['lat'], bank['lon']],
                popup=folium.Popup(popup_text, max_width=300),
                icon=folium.Icon(color='red', icon='droplet', prefix='fa')
            ).add_to(m)
            
            folium.PolyLine(
                locations=[[user_lat, user_lon], [bank['lat'], bank['lon']]],
                color='red',
                weight=2,
                opacity=0.7
            ).add_to(m)
        
        map_html = m._repr_html_()
        
        context = {
            'map': map_html,
            'nearest_banks': nearest_banks[:5],
            'blood_type': blood_type
        }
        return render(request, 'nearest_blood_bank.html', context)
    
    return render(request, 'find_nearest_bank.html', {})


def PublicBloodBankDirectory(request):
    """Public blood bank directory"""
    if request.method == 'GET':
        city = request.GET.get('city', '')
        
        try:
            con = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='root', database='lifelink', charset='utf8')
            with con:
                cur = con.cursor()
                
                query = "SELECT bank_name, address, phone, email, city FROM blood_bank WHERE latitude IS NOT NULL AND longitude IS NOT NULL"
                params = []
                
                if city:
                    query += " AND city = %s"
                    params.append(city)
                
                cur.execute(query, params)
                banks = cur.fetchall()
                
                cur.execute("SELECT DISTINCT city FROM blood_bank WHERE city IS NOT NULL ORDER BY city")
                cities = [row[0] for row in cur.fetchall()]
        except:
            banks = []
            cities = []
        
        context = {
            'banks': banks,
            'cities': cities,
            'selected_city': city
        }
        return render(request, 'public_blood_bank_directory.html', context)
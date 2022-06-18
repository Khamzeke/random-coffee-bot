import datetime
from datetime import date

import psycopg2

#conn = psycopg2.connect(dbname='dbms', user='postgres',
                        #password='root', host='localhost')
conn = psycopg2.connect("postgres://kacbkjzgftibae:2ce4001bb7782a22232485fe7c99fdbde2d5ef0274dd63c6db69e3b71e5e3117@ec2-54-228-125-183.eu-west-1.compute.amazonaws.com:5432/d1343br5270dik")
cursor = conn.cursor()


def addUser(id, data):
    deleteUser(id)
    sql = f"INSERT INTO public.users(id, fullname, city, profile, company, crole, usefulness, ready)" \
          f"VALUES ({id}, '{data['name']}', '{data['city']}', '{data['profile']}', '{data['company']}', '{data['role']}', '{data['usefulness']}', {False});"
    try:
        cursor.execute(sql)
        conn.commit()
        print(f"[LOG] User {id} added to database ")
    except:
        print("[ERROR] User not added")
        conn.rollback()


def deleteUser(id):
    sql = f"DELETE FROM public.users where id={id}"
    try:
        cursor.execute(sql)
        conn.commit()
    except:
        conn.rollback()


def getUser(id):
    sql = f"select * from users where id={id}"
    cursor.execute(sql)
    return cursor.fetchone()

def getUsers():
    sql = f"select id, fullname, city, profile, company, crole, usefulness from users"
    cursor.execute(sql)
    return cursor.fetchall()

def getAppointments():
    sql = f"select ap.hdate, u1.fullname, u2.fullname, ap.format, happened, reason from " \
          f"appointments ap join users u1 on u1.id = ap.fcompanion join users u2 on u2.id = ap.scompanion"
    cursor.execute(sql)
    return cursor.fetchall()

def updateUserStatus(id, ready):
    sql = f"UPDATE public.users	SET ready={ready}, answer_date='{date.today()}' " \
          f"WHERE id={id};"
    try:
        cursor.execute(sql)
        conn.commit()
    except:
        print("[ERROR] User status update is unsuccessful!")
        conn.rollback()


def getUsersByReadyStatus(status):
    sql = f"SELECT * FROM public.users where ready={status}"
    cursor.execute(sql)
    return cursor.fetchall()


def createAppointment(fcomp, scomp):
    sql = f"INSERT INTO public.appointments(fcompanion, scompanion, hdate)VALUES ({fcomp}, {scomp}, '{date.today()}');"
    try:
        cursor.execute(sql)
        conn.commit()
    except:
        print("[ERROR] Creating appointment failed!")
        conn.rollback()


def makeReadyStatus(id, status):
    sql = f"UPDATE public.users	SET ready = {status} WHERE id={id};"
    try:
        cursor.execute(sql)
        conn.commit()
    except:
        conn.rollback()


def getCompanionProfile(id):
    sql = f"select * from appointments where fcompanion={id} or scompanion={id} order by hdate desc"
    try:
        cursor.execute(sql)
        companion = cursor.fetchone()
        if companion[1] == id:
            id = companion[2]
        else:
            id = companion[1]
        sql = f"select * from users where id = {id}"
        cursor.execute(sql)
        return cursor.fetchone()
    except:
        conn.rollback()

def getUserLastAppointment(id):
    sql = f"select * from appointments where fcompanion = {id} or scompanion = {id} and hdate - current_date <= 7 order by id desc fetch next 1 rows only"
    cursor.execute(sql)
    appointment = cursor.fetchone()
    if appointment is not None:
        if appointment[3] is not None:
            print(f'[ERROR] Unavailable user appointment [{id}]')
            return None
    return appointment

def setAnswerDate(id, period):
    answer_date = date.today()
    if period == 'week':
        answer_date = date.today() + datetime.timedelta(days=7)
    if period == 'month':
        answer_date = date.today() + datetime.timedelta(days=28)
    sql = f"update users set answer_date='{answer_date}' where id={id}"
    try:
        cursor.execute(sql)
        conn.commit()
    except:
        conn.rollback()
        print("[ERROR] Cannot update answer date")

def clearAppointments():
    print("[INFO] Clearing appointments")
    sql = "update appointments set happened = false where happened is null"
    try:
        cursor.execute(sql)
        conn.commit()
    except:
        conn.rollback()
        print("[ERROR] Cannot set appointments not happened")

def execute(sql):
    try:
        cursor.execute(sql)
        conn.commit()
    except:
        conn.rollback()

def getUserCompanion(id):
    sql = f'select * from appointments where fcompanion = {id} or scompanion = {id} order by id desc fetch next 1 rows only'
    cursor.execute(sql)
    appointment = cursor.fetchone()
    if appointment[1] == int(id):
        companion_id = appointment[2]
    else:
        companion_id = appointment[1]
    sql = f"select * from users where id = {companion_id}"
    cursor.execute(sql)
    return cursor.fetchone()

def setAppointmentHappened(id,happened, format):
    print('[LOG] Appointment format/happened updating')
    if happened:
        sql = f"update appointments set happened={happened}, format='{format}' where id={id}"
        print(f'[LOG] Appointment was happened {format}')
    else:
        sql = f"update appointments set happened={happened}, reason='{format}' where id={id}"
        print(f'[LOG] Appointment was not happened')
    try:
        cursor.execute(sql)
        conn.commit()
    except:
        conn.rollback()
        print('[ERROR] Cannot update appointment format/reason')

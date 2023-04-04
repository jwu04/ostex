import requests, html, sqlite3, json, os, math
import pandas as pd
import __constants__ as constants
from flask import Flask, render_template, request, redirect, url_for, session
from pprint import pprint
from os import getenv

app = Flask(__name__)
API_URL = 'https://osu.ppy.sh/api/v2'
TOKEN_URL = 'https://osu.ppy.sh/oauth/token'
DB_FILE = "data.db"

db =  sqlite3.connect(DB_FILE, check_same_thread = False)

@app.route("/")
def auth():
    return render_template("welcome.html")

@app.route("/dashboard")
def dashboard():
    if 'token' in session:
        username, avatar = grabUserData(session['token'])
        stocks, spAmount = loadSP(username)
        rankings = getRankings(session['token'], 1)[0:7]
        for user in rankings:
            user[2] = round((user[2]/10)/math.sqrt(int(user[0])),2)
        return render_template("dashboard.html", username = username, avatar = avatar, sp = float(spAmount), rankings = rankings)
    return redirect("/")

@app.route("/invest", methods = ["GET", "POST"])
def invest():
    if 'token' in session:
        token = session['token']
        username, avatar = grabUserData(token)
        rankings = getRankings(token, 1)
        
        for user in rankings:
            user.append(round((user[2]/10)/math.sqrt(int(user[0])),2))
        if request.method == 'POST':
            user = request.form['osu-id']
            headers = {**constants.defaultHeader, 'Authorization': f'Bearer {token}'}
            response = requests.get(f'{API_URL}/users/{user}/osu', headers = headers)
            data = response.json()
            pprint(data, indent=2)
            searchedData = ['#' + str(data.get('statistics').get('global_rank')), \
                            data.get('username'), \
                            'o!sp' + str(round((data.get('statistics').get('pp')/10)/math.sqrt(int(data.get('statistics').get('global_rank'))),2))]
            return render_template("invest.html", username = username, avatar = avatar, rankings = rankings, searchedData = searchedData)
        return render_template("invest.html", username = username, avatar = avatar, rankings = rankings, searchedData = [])
    return redirect("/")

@app.route("/statistics")
def statistics():
    if 'token' in session:
        username, avatar = grabUserData(session['token'])

        return render_template("statistics.html", username = username, avatar = avatar)
    return redirect("/")

@app.route("/authorize", methods=['GET']) 
def authorize():
    if request.args.get('code', None) == None:
        if request.args.get('error') == 'access_denied':
            return redirect('/')
        params = {
            'client_id': 19137,
            'redirect_uri': "http://127.0.0.1:5000/authorize",
            'response_type': 'code',
            'scope': 'public',
        }
        response = requests.get('https://osu.ppy.sh/oauth/authorize', params=params, headers=constants.defaultHeader)
        return redirect(response.url)
    else:
        code = request.args.get('code')
        params = {
            'client_id': 19137,
            'client_secret': 'XUrRhF8ZA9yvkJD8xBBD3wuPss0WxDo6QcVWHBKg',
            'code' : code,
            'grant_type': 'authorization_code',
            'redirect_uri': "http://127.0.0.1:5000/authorize"
        }
        response = requests.post(TOKEN_URL, data = json.dumps(params), headers=constants.defaultHeader)
        token = response.json().get('access_token')
        session['token'] = token
        return redirect('/dashboard')

@app.route("/signout")
def signout():
    session.pop('token', default=None)
    return redirect('/')

def grabUserData(token):
    headers = {**constants.defaultHeader, 'Authorization': f'Bearer {token}'}
    response = requests.get(f'{API_URL}/me/osu', headers = headers)
    data = response.json()
    username = data.get('username')
    avatar = data.get('avatar_url')
    return username, avatar

def loadSP(username):
    db = sqlite3.connect(DB_FILE)
    c = db.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS wallet (stocks TEXT, sp INTEGER, username TEXT)')
    c.execute('SELECT username FROM wallet WHERE username = ?', (username,))
    exists = c.fetchone()
    if exists == None:
        c.execute('INSERT INTO wallet (stocks, sp, username) VALUES (?, ?, ?)', ('Empty', 5000, username))
        db.commit()
    c.execute('SELECT stocks, sp FROM wallet WHERE username = ?', (username,))
    data = c.fetchall()
    return data[0][0], data[0][1]

def getRankings(token, page):
    headers = {**constants.defaultHeader, 'Authorization': f'Bearer {token}'}
    rankingList = []
    for pageNumber in range(page+1):
        response = requests.get(f'{API_URL}/rankings/osu/performance', params = {'page' : pageNumber}, headers = headers)
        user_data = response.json().get('ranking')
        for user in user_data:
            rank = user.get('global_rank')
            pp = user.get('pp')
            username = user.get('user').get('username')
            rankingList.append([rank, username, pp])
    return rankingList
    
def getPersonalToken():
    data = {
        'client_id': 19137,
        'client_secret': 'XUrRhF8ZA9yvkJD8xBBD3wuPss0WxDo6QcVWHBKg',
        'grant_type': 'client_credentials',
        'scope': 'public'
    }

    response = requests.post(TOKEN_URL, data=data)
    return response.json().get('access_token')
#
# def main():
#     token = get_token()
#
#     headers = {
#         'Content-Type': 'application/json',
#         'Accept': 'application/json',
#         'Authorization': f'Bearer {token}'
#     }
#
#     db = sqlite3.connect(DB_FILE)
#     c = db.cursor()
#     c.execute('CREATE TABLE IF NOT EXISTS performance (rank INTEGER, pp INTEGER, username TEXT)')
#     for i in range(6):
#       params = {
#         'page' : 1 + i
#       }
#       response = requests.get(f'{API_URL}/rankings/osu/performance', params=params, headers=headers)
#       user_data = response.json().get('ranking')
#       for user in user_data:
#         rank = user.get('global_rank')
#         pp = user.get('pp')
#         username = user.get('user').get('username')
#         c.execute('SELECT username FROM performance WHERE username = ?', (username,))
#         exists = c.fetchone()
#         if exists == None:
#           c.execute('INSERT INTO performance (rank, pp, username) VALUES (?, ?, ?)', (rank, pp, username))
#         else:
#           c.execute('UPDATE performance SET rank = ?, pp = ? WHERE username = ?', (rank, pp, username))
#         db.commit()
#
#     response2 = requests.get(f'{API_URL}/me/osu', headers=headers)
#     x = response2.json()
#     print(x)
#     # c.execute('SELECT * FROM performance')
#     # data = c.fetchall()
#     # for x in data:
#     #     print(x)
#     db.close()

if __name__ == '__main__':
    app.secret_key = os.urandom(12)
    app.debug = True
    app.run()

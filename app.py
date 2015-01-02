from flask import Flask,render_template,request,session,redirect,url_for
from pymongo import MongoClient
from functools import wraps

app = Flask(__name__)

client = MongoClient()
db = client['cookedgoose']
acctdb = db['accounts']
boarddb = db['boards']

def loggedin():
    return "username" in session

def requirelogin(f):
    @wraps(f)
    def ff():
        if loggedin(): return f()
        else: return redirect("/")
    return ff

def requirelogout(f):
    @wraps(f)
    def ff():
        if not loggedin(): return f()
        else: return redirect("/")
    return ff

@app.route("/")
@app.route("/home",methods=['GET','POST'])
def home_html():
    if request.method=="POST":
        pass
    return render_template("home.html",
                           sess=session)


@app.route("/todo")
def todo_html():
    return render_template("todo.html")

@app.route("/login", methods=["GET","POST"])
@requirelogout
def login_html():
    error = []
    success = True
    post = False
    if(request.method=="POST"):
        post = True
        loguser = request.form["username"]
        logpass = request.form["password"]
        acct = acctdb.find_one({"login":loguser})
        if not acct:
            error.append("no user with that name")
        else:
            if acct["password"]!=logpass:
                error.append("wrong username or password")
        if len(error)>0:
            success = False
        else:
            session["username"] = loguser
            return redirect("/")
    return render_template("login.html",
                           errorlist=error, 
                           success=success,
                           post=post,
                           sess=session)

@app.route("/logout")
@requirelogin
def logout_html():
    session.pop('username',None)
    return redirect('/')

@app.route("/register", methods=["GET","POST"])
@requirelogout
def register_html():
    if(request.method=="POST"):
        newuser = request.form["username"]
        newpass = request.form["password"]
        newpass2 = request.form["pwdconfirm"]
        error = []
        success = True
        post = True
        
        if newpass!=newpass2:
            error.append("mismatched password")
        if newuser=="jamal":
            error.append("you are jamal")
        if newuser=="Anonymous":
            error.append("no")
        if acctdb.find_one({"login":newuser}):
            error.append("user with that name already exists")
        if len(error)>0:
            success = False
        else:
            newAccount = {"login":newuser,"password":newpass}
            acctdb.insert(newAccount)
        return render_template("register.html",
                               errorlist=error,
                               success=success,
                               post=post)
    else:
        return render_template("register.html")

@app.route("/boards",methods=['GET','POST'])
def boards_html():
    errors = []
    post = False
    success = True
    if request.method=="POST":
        post = True
        newtitle = request.form["title"]
        newid = boarddb.count()+1
        if boarddb.find_one({"title":newtitle}):
            errors.append("board with that title already exists")
        if len(errors)>0:
            success = False
        else:
            newboard = {"title":newtitle,"owner":session["username"],"id":newid}
            boarddb.insert(newboard)
    boards = boarddb.find()
    return render_template("boards.html",
                           errorlist=errors,
                           post=post,
                           success=success,
                           boards=sorted(boards,key=lambda k:k["id"] if "id" in k else 0,reverse=True),
                           sess=session)

@app.route("/board/<title>",methods=['GET','POST'])
def board_html(title):
    errors = []
    post = False
    if request.method=="POST":
        post = True
    return render_template("board.html",
                           errorlist=errors,
                           post=post,
                           sess=session,
                           board=boarddb.find_one({"title":title}))

@app.route("/settings",methods=['GET','POST'])
@requirelogin
def settings_html():
    errors = []
    post = False
    success = True
    if request.method=="POST":
        post = True
        oldpass = request.form["oldpass"]
        newpass = request.form["newpass"]
        passcfm = request.form["passcfm"]
        curacct = acctdb.find_one({"login":session["username"]})
        curpass = curacct["password"]
        if oldpass!=curpass:
            errors.append("incorrect password")
        if newpass!=passcfm:
            errors.append("new passwords don't match")
        if len(errors)>0:
            success = False
        else:
            curacct["password"] = newpass
            acctdb.save(curacct)
    return render_template("settings.html",
                           errorlist=errors,
                           post=post,
                           success=success,
                           sess=session)

###

if __name__ == "__main__":
    app.debug = True
    app.secret_key = "insane"
    app.run()
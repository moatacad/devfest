from datetime import datetime
from flask import render_template,abort,request,redirect,flash,url_for,session
from werkzeug.security import generate_password_hash, check_password_hash
from pkg import app
from pkg.models import db,Admin,Level,Breakout

from pkg.forms import BreakoutForm


@app.route("/admin/dashboard")
def admin_dashboard():
    return render_template("admin/dashboard.html")


@app.route("/admin/addtopics",methods=['POST',"GET"])
def admin_addtopic():
    bform = BreakoutForm()
    devs = db.session.query(Level).all()
    if request.method =="GET":        
        return render_template("admin/addtopic.html",bform=bform,devs=devs) 
    else:
        if bform.validate_on_submit():
            title = bform.title.data
            # status = bform.status.data
            status = request.form.get('status')
            level = request.form.get('level')
            file = bform.image.data
            filename = bform.image.data.filename
            #you can set a new file name here if you wish
            file.save(f"pkg/static/uploads/{filename}")   
            topic = Breakout(break_title=title,break_image=filename,break_status=status,break_level=level)
            db.session.add(topic)
            db.session.commit()
            return redirect(url_for('breakouts'))
        else:
            return render_template("admin/addtopic.html",bform=bform,devs=devs)






    
    
@app.route("/admin/breakouts")
def breakouts():
    alltopics = db.session.query(Breakout).all()
    return render_template('admin/breakout.html',alltopics=alltopics) #extend admin_layout in breakout.html







@app.route("/admin/login/",methods=['POST',"GET"])
def admin_login():
    if request.method =="GET":
        return render_template("admin/login.html")
    else:#retrieve form data
        email = request.form.get('email')
        pwd = request.form.get('pwd') 
        
        admin = db.session.query(Admin).filter(Admin.admin_username ==email).first()
        if admin !=None: #check password
            saved_pwd = admin.admin_pwd
            check = check_password_hash(saved_pwd,pwd)
            if check:
                session['adminonline'] = admin.admin_id
                flash("Welcome!",category='success')
                return redirect(url_for('admin_dashboard')) #create this route!
            else:
                flash("Invalid credentials",category='error')
                return redirect(url_for('admin_login'))
        else:
                flash("Invalid credentials",category='error')
                return redirect(url_for('admin_login'))




@app.route("/admin/")
def admin_home():  
     
    return "done"
    
    


    
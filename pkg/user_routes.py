from datetime import datetime
import requests,json
import os,random,string
from functools import wraps
from flask import render_template,abort,request,redirect,flash,url_for,make_response,session

from werkzeug.security import generate_password_hash, check_password_hash
from pkg import app
from pkg.models import db,User,Level,Donation,Breakout,UserRegistration


def get_hotels():
    #we want to connect to the endpoint, get list of hotels and send to the template
    try:
        url = "http://127.0.0.1:3000/api/v1/listall/"
        response = requests.get(url)
        data = response.json()
        return data
    except:
        return None    
    

def login_required(f):
    @wraps(f) #this ensures that details(such as __name__) about the original function f, that is being decorated is still available...
    def check_login(*args, **kwargs):
        if session.get("useronline") !=None:
           return f(*args, **kwargs) 
        else:
            flash("You must be logged in to access this page",category="error")
            return redirect(url_for("login_page"))
    return check_login

@app.route("/")
def home_page():   
    hotels = get_hotels()
    if session.get("useronline") !=None:
        id = session.get('useronline')
        deets = User.query.get(id)
    else:
        deets = None
    return render_template("user/index.html",deets=deets,hotels=hotels) 



@app.route("/topaystack",methods=['POST'])
@login_required
def topaystack():
    id = session.get('useronline')
    ref = session.get('ref')
    if ref:
        url="https://api.paystack.co/transaction/initialize"        
        headers = {"Content-Type": "application/json","Authorization":"Bearer sk_test_3c5244cfb8965dd000f07a4cfa97185aab2e88d5"}
                
        trasaction_deets = Donation.query.filter(Donation.donate_ref==ref).first()
                
        data={"email": trasaction_deets.donate_email, "amount": trasaction_deets.donate_amt * 100,"reference":ref,"callback_url":"https://127.0.0.1:8080/paylanding"}
        response = requests.post(url,headers=headers,data=json.dumps(data)) 
        rspjson = response.json()
        if rspjson and rspjson.get('status') == True:
            authurl = rspjson['data']['authorization_url']
            return redirect(authurl)  
        else:
            flash(rspjson['message'])
            return redirect('/donation')              
    else:
        flash("Start the payment process again")
        return redirect('/donation')

@app.route("/breakout",methods=['POST','GET'])
@login_required
def breakout():
    id = session.get('useronline')
    deets = User.query.get(id) #deets.user_levelid
    if request.method =='GET':
        topics = Breakout.query.filter(Breakout.break_status==1,Breakout.break_level==deets.user_levelid).all()        
        # regtopics = UserRegistration.query.filter(UserRegistration.userid==id).all()
        
        regtopics = [x.break_id for x in deets.myregistrations] #[<UserRegistration 1>, <UserRegistration 2>]
        
        return render_template("user/mybreakout.html", deets=deets,topics=topics,regtopics=regtopics)
    else:#retrieve the form data
        mytopics = request.form.getlist('topicid') #returns the id as a list        
        if mytopics:
            #delete his previous registrations before you insert
            db.session.execute(db.text(f"DELETE FROM user_registration WHERE userid={id}"))
            db.session.commit()
                        
            for t in mytopics:
                user_reg = UserRegistration(userid=id,break_id=t)
                db.session.add(user_reg)
            db.session.commit()
            flash('Your registration was successful')      
            return redirect('/dashboard')
        else:
            flash('You must choose a topic')
            return redirect("/breakout")    
    
    
@app.route("/paylanding")
@login_required
def paylanding():
    '''We will receive ref number from paystack , call another endpooint to verify the status of the transaction, based on that.. we will update our database. End!'''
    
    id = session.get('useronline')
    trxref = request.args.get('trxref')
    if (session.get('ref') !=None and trxref == session.get('ref')):
        url = "https://api.paystack.co/transaction/verify/"+ str(session.get('ref'))
        
        headers = {"Content-Type": "application/json","Authorization":"Bearer sk_test_3c5244cfb8965dd000f07a4cfa97185aab2e88d5"}
        
        response= requests.get(url,headers=headers)
        rsp = response.json()
        return rsp
    else:
        return redirect("/donation")
    
    

@app.route('/donation', methods=['POST',"GET"])
@login_required
def donation():
    id = session.get('useronline')
    if request.method =='GET':
        deets = User.query.get(id)
        return render_template('user/donations.html',deets=deets)
    else:
        fullname = request.form.get('fullname')
        email = request.form.get('email')
        amt = request.form.get('amt')
        #generate a transaction ref number and save it in a session variable
        ref = str(int(random.random() * 10000000000)) 
        session['ref'] = ref
        
        if fullname !="" and email !="" and amt !="":
            donate = Donation(donate_donor=fullname,donate_amt = amt, donate_email=email,donate_status='pending',donate_userid=id,donate_ref=ref)
            db.session.add(donate)
            db.session.commit()
            if donate.donate_id:
                return redirect('/confirm') #create a route '/confirm
            else:
                flash('Please complete the form')
                return redirect('/donation')
        else:
            flash('Please complete the form')
            return redirect('/donation')

@app.route("/confirm") 
@login_required
def confirm():
    id = session.get('useronline')
    deets = User.query.get(id)
    #details of the donation will be available through session.get('ref)
    ref= session.get('ref')
    if ref:
        donation_deets = Donation.query.filter(Donation.donate_ref==ref).first()
        return render_template("user/confirm.html",deets=deets,donation_deets=donation_deets)
    else:
        flash("Please start the transaction again")
        return redirect('/donation')
        
    
    


@app.route("/changedp",methods=['POST','GET'])
@login_required
def change_dp():
    id = session.get('useronline')
    deets = User.query.get(id) 
    oldpix=deets.user_pix 
    if request.method=='GET':
        return render_template("user/changedp.html",deets=deets) #go and extend home_layout in changedp.html
    else:
        dp = request.files.get("dp")
        filename = dp.filename #empty if no file was selected for upload        
        if filename =="":
            flash("Please select a file",category='error')
            return redirect("/changedp")
        else:                
            name,ext =  os.path.splitext(filename)
            allowed = ['.jpg','.png','.jpeg']
            if ext.lower() in allowed:
                final_name = int(random.random() * 1000000)
                final_name = str(final_name) + ext #we cant concatenate int and str
                dp.save(f"pkg/static/profile/{final_name}") 
                user = db.session.query(User).get(id) #save in database
                user.user_pix = final_name
                db.session.commit()
                try:
                    os.remove(f"pkg/static/profile/{oldpix}")
                except:
                    pass
                flash("Profile picture added",category='success') 
                return redirect("/dashboard")
            else:
                flash("extension not allowed",category='error')
                return redirect("/changedp")
    
    
    
    
    
    
    
    
    

@app.route('/profile',methods=['POST','GET'])
@login_required
def user_profile():
    id = session.get('useronline')
    if request.method =='GET':
        deets = User.query.get(id)
        devs = db.session.query(Level).all()    
        return render_template('user/profile.html',devs=devs,deets=deets) #{{ deets }}
    else: 
        level = request.form.get('level')
        phone= request.form.get('phone')
        lname= request.form.get('lname')
        fname=request.form.get('fname')
        user = db.session.query(User).get(id)
        user.user_fname=fname
        user.user_lname=lname
        user.user_phone=phone
        user.user_levelid=level
        db.session.commit()
        flash("Profile updated",category="success")           
        return redirect(url_for("user_profile"))
 


    
@app.route("/dashboard")
@login_required
def user_dashboard():
    hotels = get_hotels()
    id = session.get('useronline')
    deets = User.query.get(id)
    return render_template("user/dashboard.html",deets=deets,hotels=hotels) 
    

@app.route("/login", methods=['POST','GET'])
def login_page():
    if request.method=='GET':
        return render_template("user/loginpage.html")
    else: #retrieve
        email= request.form.get('email')
        pwd = request.form.get('pwd')
        record = db.session.query(User).filter(User.user_email ==email).first() 
        if record:
            hashed_pwd = record.user_password #the one on the table
            rsp = check_password_hash(hashed_pwd,pwd)
            if rsp:
                id = record.user_id
                session['useronline'] = id
                return redirect(url_for('user_dashboard'))
            else:
                flash("Invalid Credentials",category='error')
                return  redirect("/login")
        else:
                flash("Invalid Credentials",category='error')
                return  redirect("/login")
        

@app.route("/logout")
def logout():
    if session.get("useronline") !=None:
        session.pop("useronline",None)
    return redirect("/")



@app.route("/register",methods=['POST','GET'])
def user_register():
    if request.method =='GET':
        return render_template("user/register.html")
    else:#retrieve form fields:
        state= request.form.get('state')
        lga= request.form.get('lga')
        fname= request.form.get('fname')
        lname= request.form.get('lname')
        email= request.form.get('email')
        pwd= request.form.get('pwd')
        hashed_pwd = generate_password_hash(pwd)
        if email !="" and state !='' and lga !='':
            user = User(user_fname=fname,user_lname=lname,user_email=email,user_password=hashed_pwd,user_stateid=state,user_lgaid=lga)
            #insert into dabase
            db.session.add(user) 
            db.session.commit() 
            id = user.user_id
            #log the user in and redirect to the dashboard
            session['useronline'] = id
            return redirect(url_for("user_dashboard"))
        else:
            flash("Some of the form fields are blank",category="error")
            return redirect(url_for("user_register"))






    
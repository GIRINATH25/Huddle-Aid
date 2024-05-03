from flask import Flask,render_template,request,redirect,url_for,session,Response
from flask_mysqldb import MySQL
import moviepy.editor as mp
import speech_recognition as sr
import MySQLdb.cursors
import os

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/path/to/your/credentials.json"

app=Flask(__name__)
app.secret_key='qwer'

app.config['MYSQL_HOST'] = "localhost"
app.config['MYSQL_USER'] = "root"
app.config['MYSQL_PASSWORD'] = "mysql"
app.config['MYSQL_DB'] = "pro"

mysql = MySQL(app)

@app.route('/register.html',methods=['GET','POST'])
def register():
    if request.method == 'POST':
        reg=request.form
        name=reg['name']
        email=reg['email']
        password=reg['password']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO user(name,email,password) VALUES(%s, %s, %s)",(name, email, password))
        mysql.connection.commit()
        cur.close()
        return render_template('login.html')
    return render_template('register.html')

@app.route('/',methods=['GET','POST'])
@app.route('/login.html',methods=['GET','POST'])
def login():
    s=''
    if request.method=='POST' and 'email' in request.form and 'password' in request.form:
        email=request.form['email']
        password=request.form['password']
        cur=mysql.connection.cursor(MySQLdb.cursors.DictCursor)    
        cur.execute("select * from user where email=%s and password=%s",(email,password, ))
        user = cur.fetchone()
        if user:
            session['loggedin']=True
            session['name']=user['name']
            session['email']=user['email']
            session['password']=user['password']
            return render_template('create.html')
        else:
            s='Please enter valid email/password!'        
    
    return render_template('login.html',s=s)

@app.route('/create.html')
def create():
    return render_template('create.html')

ALLOWED_EXTENSIONS = ['mp4']

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/final.html', methods=['POST'])
def upload():
    if 'video' not in request.files:
        return 'No video file found'
    video = request.files['video']
    if video.filename == '':
        return 'No video selected'
    if video and allowed_file(video.filename):
        video.save('static/videos/' + "Input.mp4")
        return render_template('final.html', video_name="Input.mp4")
    return 'Invalid video file'

@app.route('/output.html')
def output():
    return render_template('output.html')

@app.route('/cut.html', methods=['POST'])
def cut():
    try:
        # Load the video
        video = mp.VideoFileClip("static/videos/input.mp4")

        # Extract the audio from the video
        audio = video.audio
        audio.write_audiofile("audio.wav")

        # Recognize the speech in the audio
        recognizer = sr.Recognizer()
        with sr.AudioFile("audio.wav") as source:
            audio = recognizer.record(source)
            transcript = recognizer.recognize_google(audio)

        # Get the start and end words from the user
        start = request.form['start']
        end = request.form['end']

        # Check if transcript is available
        if transcript:
            start_time = transcript.find(start) / len(transcript) * video.duration
            end_time = transcript.find(end) / len(transcript) * video.duration
        else:
            return "Transcript not available"

        # Cut the video
        cut_video = video.subclip(start_time, end_time)

        # Save the cut video
        cut_video.write_videofile("output.mp4")

        return render_template('cut.html')

    except Exception as e:
        return f"An error occurred: {str(e)}"


if __name__=="__main__":
    app.run(debug=True)
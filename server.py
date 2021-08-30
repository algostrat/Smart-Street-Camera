"""

Before running server you must run the following commands within a python console in cwd
in order to create the SQL table within data.sqlite

'
from streetlight_server import db
db.create_all()
'

"""

from flask import Flask, request, jsonify, render_template, flash, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from base64 import b64encode
import base64
import os
from io import BytesIO  # Converts data from Database into bytes

basedir = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data.sqlite')
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = basedir
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'dev'
db = SQLAlchemy(app)
# db.create_all()

# Picture table. By default the table name is filecontent
class FileContent(db.Model):
    """
    The first time the app runs you need to create the table. In Python
    terminal import db, Then run db.create_all()
    """
    """ ___tablename__ = 'yourchoice' """  # You can override the default table name

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    data = db.Column(db.LargeBinary, nullable=False)  # Actual data, needed for Download
    rendered_data = db.Column(db.Text, nullable=False)  # Data to render the pic in browser
    text = db.Column(db.Text)
    # location = db.Column(db.String(64))
    pic_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'Pic Name: {self.name} Data: {self.data} text: {self.text} created on: {self.pic_date} location: {self.location}'


def render_picture(data):
    render_pic = base64.b64encode(data).decode('ascii')
    return render_pic


@app.route("/api/upload", methods=["POST"])
def process_image():
    # read image file string data
    file = request.files['image']
    data = file.read()
    render_file = render_picture(data)
    text = request.form['mph']
    name = request.form['name']
    file.save('static/img/'+name)
    # location = request.form['mph']
    pic_date = request.form['timestamp']
    pic_date = datetime.strptime(pic_date, "%m/%d/%Y %H:%M:%S")

    newFile = FileContent(name=name, data=data, rendered_data=render_file, text=text, pic_date=pic_date)
    db.session.add(newFile)
    db.session.commit()

    with open('static/img/'+name, 'wb') as fid:
        fid.write(data)

    return jsonify({'msg': 'success', 'size': 'not defined'})


@app.route('/')
def index():
    image_names = os.listdir('static/img/')
    data = FileContent.query.order_by(FileContent.pic_date.desc()).all()
    return render_template('home.html', data=data)


@app.route('/delete/<int:id>')
def delete(id):
    task_to_delete = FileContent.query.get_or_404(id)

    os.remove('static/img/' + task_to_delete.name)
    try:
        db.session.delete(task_to_delete)
        db.session.commit()
        return redirect('/')
    except:
        return 'There was a problem deleting that photo'


if __name__ == "__main__":
    app.run(host="10.0.0.182", port=5000)
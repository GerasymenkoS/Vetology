import os
import random
import string

import collections

import elasticsearch
from flask import Flask
from flask import render_template
from flask import send_from_directory
from werkzeug.utils import secure_filename

from search import WorkWithSignatures
from flask import request
import csv, io
from ast import literal_eval

UPLOAD_FOLDER = '/tmp' #'/app/images'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__, static_url_path='/images/')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

sign = WorkWithSignatures()

@app.route('/images/<path:path>')
def send_iamges(path):
    return send_from_directory(UPLOAD_FOLDER, path)

@app.route('/js/<path:path>')
def send_js(path):
    return send_from_directory('templates/js', path)

@app.route('/css/<path:path>')
def send_css(path):
    return send_from_directory('templates/css', path)


@app.route("/")
def main_page():
    return render_template('index.html')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/load_csv/", methods=['GET', 'POST'])
def load_csv_file():
    if request.method == 'POST':
        if request.files['csv_file']:
            try:
                csv_file = io.StringIO(request.files['csv_file'].stream.read().decode("UTF8"), newline=None)
                path_reader = csv.reader(csv_file, delimiter=' ', quotechar='|')
                for path in path_reader:
                    sign.load_file(path[0].replace(',', '/'))
            except Exception as e:
                return "Wrong " + str(e)
            return "OK"
        else:
            return render_template('load_csv.html')
    else:
        return render_template('load_csv.html')


@app.route("/params/", methods=['GET', 'POST'])
def params():
    if request.method == 'POST':
        params_dict = {'n_grid': 9,
                       'crop_percentile': (5, 95),
                       'P': None,
                       'diagonal_neighbors': True,
                       'identical_tolerance': 2/255,
                       'n_levels': 2}
        f = request.form
        try:
            params_dict['n_grid'] = int(f['n_grid'])
            params_dict['crop_percentile'] = literal_eval(f['crop_percentile'])
            params_dict['P'] = int(f['P']) if f['P'] else None
            params_dict['diagonal_neighbors'] = bool(f.get('diagonal_neighbors'))
            params_dict['search_rotated'] = bool(f.get('search_rotated'))
            params_dict['identical_tolerance'] = float(f['identical_tolerance'])
            params_dict['n_levels'] = int(f['n_levels'])
        except ValueError as e:
            print(e)
            return "Incorrect params"
        except Exception as e:
            return "Wrong"
        else:
            sign.reload_params(params_dict)
            return "OK"
    else:
        p = sign.get_all_params()
        print(p)
        return render_template('params.html', **sign.get_all_params())


@app.route("/load_images/", methods=['GET', 'POST'])
def load_new_file():
    print(request.method)
    if request.method == 'POST':
        files = request.files.getlist('file')
        if files:
            for file in files:
                if file.filename == '':
                    return render_template('load.html')
                if file and allowed_file(file.filename):
                    try:
                        salt = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))
                        filename = str(salt) + secure_filename(file.filename)
                        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        file.save(file_path)
                        sign.load_file(file_path)
                    except Exception as e:
                        return "Wrong: " + str(e)
            return "OK"
        else:
            return render_template('load.html')
    else:
        return render_template('load.html')

@app.route("/clear/", methods=['GET'])
def clear():
    sign.clear_db()
    return "Deleted"


Result = collections.namedtuple('Result', 'number answ')

@app.route("/search/", methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        files = request.files.getlist('file')
        if files:
            files = request.files.getlist('file')
            result = []
            index = 1
            for file in files:
                if file.filename:
                    f = file.read()
                    try:
                        if request.form['search_limit']:
                            limit = int(request.form['search_limit'])
                            search_answ = sign.search_file(f)[0:limit]
                        else:
                            search_answ = sign.search_file(f)
                        result.append(Result(number=index, answ=search_answ))
                        index += 1

                    except elasticsearch.exceptions.NotFoundError as e:
                        return "DB is empty"
                    except ValueError as e:
                        print(e)
                        return "Incorrect parameter: " + str(e)
                else:
                    continue

            return render_template('result.html', result=result)
        else:
            return render_template('search.html')
    else:
        return render_template('search.html')

if __name__ == '__main__':
    app.run()

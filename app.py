from flask import Flask, render_template, redirect, url_for, session, request, jsonify
import random
import csv
import os
from datetime import datetime
import uuid
import re



app = Flask(__name__)
app.secret_key = "supersecretkey"

inner_pages = {'page1', 'page2', 'page3'}
delay_pages = { 'video1.mp4', 'video2.mp4', 'video3.mp4'}

pinLogin = ""
patternLogin = ""

ORDERED_MATCH = False

def init_errors():
    if 'errors' not in session:
        session['errors'] = {}

def is_strong_password(password):
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'[0-9]', password):
        return False
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False

    return True

def log_time_to_csv(method, phase, time_taken, pass_length):
    log_path = "password_timings.csv"
    participant_id = session['participant_id']  
    timestamp = datetime.now().isoformat()
    errors = session.get('errors', {}).get((method, phase), 0)

    row = [participant_id, method, timestamp, phase, time_taken, pass_length, errors]

    file_exists = os.path.exists(log_path)
    with open(log_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["participant_id", "method", "timestamp", "phase", "time_taken_sec", "pwd_length", "errors"])
        writer.writerow(row)


@app.route('/save_demographics', methods=['POST'])
def save_demographics():
    participant_id = str(uuid.uuid4())[:8]  # short random ID
    session['participant_id'] = participant_id

    demographics = {
        'participant_id': participant_id,
        'name': request.form.get('name'),
        'age': request.form.get('age'),
        'gender': request.form.get('gender'),
        'pronouns': request.form.get('pronouns'),
        'accessibility': request.form.get('accessibility')
    }

    # Save to demographics.csv
    file_path = 'demographics.csv'
    file_exists = os.path.exists(file_path)
    with open(file_path, 'a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=demographics.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(demographics)

    return redirect(url_for('start_random'))



@app.route('/')
def index():
    session.clear()
    session['visited'] = []
    session['distractors'] = []
    session['participant_id'] = ''
    return render_template('index.html')


# Currently index.html sends us to this page so differentiate with a specific survey page that is called instead of go_to_next
@app.route('/next')
def go_to_next():
    visited = session.get('visited', [])
    unvisited = list(inner_pages - set(visited))

    if not unvisited:
        next_page = url_for('final_survey')
    else:
        next_page = url_for('navigate', page=random.choice(unvisited))

    return render_template('survey.html', page=next_page)

@app.route('/final_survey')
def final_survey():
    return render_template('final_survey.html', done=url_for('done'))    

@app.route('/partic')
def partic():
    return session.get('participant_id', [])


@app.route('/<page>')
def navigate(page):
    if page not in inner_pages:
        return "Page not found", 404

    visited = session.get('visited', [])
    if page not in visited:
        visited.append(page)
        session['visited'] = visited

    print(visited)
    return render_template(f"{page}.html")



@app.route('/done')
def done():
    return render_template('done.html')



@app.route('/pin')
def pin():
    phase = session.get('pin_phase', 'create')
    return render_template('pin.html', login=(phase == 'login'))







@app.route('/submit_pin', methods=['POST'])
def submit_pin():
    data = request.json
    pin = data.get('pin')
    time_taken = data.get("time_taken")
    phase = session.get("pin_phase", "create")
    method = "Pin"

    init_errors()
    key = (method, phase)

    if len(pin) < 4:
        session['errors'][key] = session['errors'].get(key, 0) + 1
        return jsonify({'success': False, 'error': 'PIN must be at least 4 digits'})

    if phase == "create":
        session['pin'] = pin
        session['pin_phase'] = 'confirm'
        log_time_to_csv(method, phase, time_taken, len(pin))
        return jsonify({'status': 'confirm'})

    elif phase == "confirm":
        if pin == session.get('pin'):
            session['pin_phase'] = 'login'
            log_time_to_csv(method, phase, time_taken, len(pin))
            return jsonify({'status': 'saved', 'next': url_for('delay')})
        else:
            session['errors'][key] = session['errors'].get(key, 0) + 1
            session['pin_phase'] = 'create'
            return jsonify({'status': 'mismatch'})

    elif phase == 'login':
        if pin == session.get('pin'):
            log_time_to_csv(method, phase, time_taken, len(pin))
            return jsonify({'success': True, 'next': url_for('go_to_next')})
        else:
            session['errors'][key] = session['errors'].get(key, 0) + 1
            return jsonify({'success': False, 'error': 'Incorrect PIN'})












@app.route('/pattern')
def pattern():
    phase = session.get('pattern_phase', 'create')
    return render_template('pattern.html', phase=phase)


@app.route('/submit_pattern', methods=['POST'])
def submit_pattern():
    data = request.json
    pattern = data.get('pattern')
    phase = session.get('pattern_phase', 'create')
    method = "Pattern"

    init_errors()
    key = (method, phase)

    pattern_str = str(pattern)
    if len(pattern_str) < 4:
        session['errors'][key] = session['errors'].get(key, 0) + 1
        return jsonify({'success': False, 'error': 'Pattern must be at least 4 dots'})

    time_taken = data.get("time_taken")

    if phase == 'create':
        session['pattern'] = pattern
        session['video'] = random.choice(list(delay_pages))
        session['pattern_phase'] = 'confirm'
        log_time_to_csv(method, phase, time_taken, len(pattern_str))
        return jsonify({'status': 'confirm'})

    elif phase == 'confirm':
        if pattern == session.get('pattern'):
            session['pattern_phase'] = 'login'
            log_time_to_csv(method, phase, time_taken, len(pattern_str))
            return jsonify({'status': 'saved', 'next': url_for('delay')})
        else:
            session['errors'][key] = session['errors'].get(key, 0) + 1
            session['pattern_phase'] = 'create'
            return jsonify({'status': 'mismatch'})

    elif phase == 'login':
        if pattern == session.get('pattern'):
            log_time_to_csv(method, phase, time_taken, len(pattern_str))
            return jsonify({'success': True, 'next': url_for('reset_pattern')})
        else:
            session['errors'][key] = session['errors'].get(key, 0) + 1
            return jsonify({'success': False, 'error': 'Incorrect pattern. Try again.'})





@app.route("/image_password")
def image_password():
    phase = session.get('image_phase', 'create')

    if phase == 'login':
        correct = session.get("image_password", [])
        correct = [int(i) for i in correct]
        all_images = list(range(1, 37))  # IDs from 1 to 36
        distractors = session.get('distractors', [])
        print("Pre-Session")
        print(len(distractors))

        if len(distractors) == 0:
            distractors = list(set(all_images) - set(correct))  # exclude the 5 correct ones
            print(correct)
            print(len(distractors))
            random.shuffle(distractors)

            distractors = distractors[:(16 - len(correct))]
            session['distractors'] = distractors 

        print("################################################")
        print(distractors)
        grid = correct + distractors    # total of 16
        random.shuffle(grid)            # shuffle for randomness
    else:
        grid = list(range(1, 37))  # Full 6x6 grid for setup/confirm
        # random.shuffle(grid)

    return render_template(
        "image_password.html",
        phase=phase,
        grid=grid,
        correct=session.get("image_password")
    )

@app.route("/submit_image_login", methods=["POST"])
def submit_image_login():
    data = request.json
    attempt = data.get("sequence")
    correct = session.get("image_password", [])
    time_taken = data.get("time_taken")
    method = "Image"
    phase = "login"

    init_errors()
    key = (method, phase)

    if set(attempt) == set(correct):
        log_time_to_csv(method, phase, time_taken, len(correct))
        return jsonify({"success": True, "next": url_for("go_to_next")})
    else:
        session['errors'][key] = session['errors'].get(key, 0) + 1
        return jsonify({"success": False, "message": "Incorrect images selected"})


@app.route("/submit_image_password", methods=["POST"])
def submit_image_password():
    data = request.json
    sequence = list(map(str, data.get('sequence')))
    phase = session.get("image_phase", "create")
    method = "Image"

    init_errors()
    key = (method, phase)

    if len(sequence) < 4:
        session['errors'][key] = session['errors'].get(key, 0) + 1
        return jsonify({'success': False, 'error': 'Must select at least 4 images.'})

    time_taken = data.get("time_taken")

    if phase == "create":
        session["image_password"] = sequence
        session["image_phase"] = "confirm"
        log_time_to_csv(method, phase, time_taken, len(sequence))
        return jsonify({"status": "confirm"})

    elif phase == "confirm":
        stored = session.get("image_password", [])
        if set(sequence) == set(stored):
            session["image_phase"] = "login"
            log_time_to_csv(method, phase, time_taken, len(sequence))
            return jsonify({"status": "saved", "next": url_for("delay")})
        else:
            session['errors'][key] = session['errors'].get(key, 0) + 1
            session["image_phase"] = "create"
            return jsonify({"status": "mismatch"})





@app.route('/delay')
def delay():
    mp4 = session.get('video')
    referrer = request.referrer or url_for('pin')
    return render_template('delay.html', video=mp4, return_url=referrer)




@app.route('/reset_pin')
def reset_pin():
    visited = session['visited']
    participant_id = session['participant_id']
    session.clear()
    session['visited'] = visited
    session['participant_id'] = participant_id
    return redirect(url_for('pin'))




@app.route('/reset_pattern')
def reset_pattern():
    visited = session['visited']
    participant_id = session['participant_id']
    session.clear()
    session['visited'] = visited
    session['participant_id'] = participant_id
    return redirect(url_for('pattern'))




@app.route("/reset_image_password")
def reset_image_password():
    visited = session['visited']
    participant_id = session['participant_id']
    session.clear()
    session['visited'] = visited
    session['participant_id'] = participant_id
    return redirect(url_for("image_password"))


@app.route('/start_random')
def start_random():
    choice = random.choice(['page1', 'page2', 'page3'])
    visited = session.get('visited', [])

    visited.append(choice)
    session['visited'] = visited

    return redirect(url_for('navigate', page=choice))



## Potential String Password Phase??
@app.route('/reset_password')
def reset_password():
    session['password_phase'] = 'create'
    return redirect(url_for('password'))

@app.route('/password')
def password():
    phase = session.get('password_phase', 'create')
    return render_template('password.html', phase=phase)

@app.route('/submit_password', methods=['POST'])
def submit_password():
    data = request.json
    password = data.get('password')
    time_taken = data.get('time_taken')
    phase = session.get('password_phase', 'create')
    method = "Password"

    init_errors()
    key = (method, phase)

    if phase == 'create' and not is_strong_password(password):
        session['errors'][key] = session['errors'].get(key, 0) + 1
        return jsonify({'success': False, 'error': 'Password must be at least 8 characters long and include uppercase letters, lowercase letters, numbers and symbol.'})

    if phase == "create":
        session['password'] = password
        session['password_phase'] = 'confirm'
        log_time_to_csv(method, phase, time_taken, len(password))
        return jsonify({'status': 'confirm'})

    elif phase == "confirm":
        print(type(password))
        print(type(session.get('password')))
        print(password == session.get('password'))
        if password == session.get('password'):
            session['password_phase'] = 'login'
            log_time_to_csv(method, phase, time_taken, len(password))
            return jsonify({'success': True, 'next': url_for('delay')})
        else:
            session['errors'][key] = session['errors'].get(key, 0) + 1
            session['password_phase'] = 'create'
            return jsonify({'status': 'mismatch'})

@app.route('/submit_password_login', methods=['POST'])
def submit_password_login():
    data = request.json
    password = data.get('password')
    time_taken = data.get('time_taken')
    method = "Password"
    phase = "login"

    init_errors()
    key = (method, phase)

    if password == session.get('password'):
        log_time_to_csv(method, phase, time_taken, len(password))
        return jsonify({'success': True, 'next': url_for('go_to_next')})
    else:
        session['errors'][key] = session['errors'].get(key, 0) + 1
        return jsonify({'success': False, 'error': 'Incorrect password.'})




if __name__ == '__main__':
    app.run(debug=True)
    distractors = []
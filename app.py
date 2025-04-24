from flask import Flask, render_template, redirect, url_for, session, request, jsonify
import random
import csv
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"

inner_pages = {'page1', 'page2', 'page3'}
delay_pages = {'video1.mp4', 'video2.mp4'}

pinLogin = ""
patternLogin = ""

ORDERED_MATCH = False

def log_time_to_csv(method, phase, time_taken):
    log_path = "password_timings.csv"
    session_id = session.get('user_id', request.remote_addr)
    timestamp = datetime.now().isoformat()

    row = [method, timestamp, session_id, phase, time_taken]

    file_exists = os.path.exists(log_path)
    with open(log_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["method", "timestamp", "session_id", "phase", "time_taken_sec"])
        writer.writerow(row)


@app.route('/')
def index():
    session.clear()
    session['visited'] = []
    session['distractors'] = []
    return render_template('index.html')

@app.route('/next')
def go_to_next():
    visited = session.get('visited', [])
    unvisited = list(inner_pages - set(visited))

    if not unvisited:
        return redirect(url_for('done'))

    next_page = random.choice(unvisited)
    return redirect(url_for('navigate', page=next_page))

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
    log_time_to_csv("pin", phase, time_taken)

    if phase == "create":
        session['pin'] = pin
        session['pin_phase'] = 'confirm'
        return jsonify({'status': 'confirm'})

    elif phase == "confirm":
        if pin == session.get('pin'):
            session['pin_phase'] = 'login'
            return jsonify({'status': 'saved', 'next': url_for('delay')})
        else:
            session['pin_phase'] = 'create'
            return jsonify({'status': 'mismatch'})

    elif phase == 'login':
        if pin == session.get('pin'):
            return jsonify({'success': True, 'next': url_for('go_to_next')})
        else:
            return jsonify({'success': False, 'error': 'Incorrect PIN'})

@app.route('/pattern')
def pattern():
    phase = session.get('pattern_phase', 'create')
    return render_template('pattern.html', phase=phase)

@app.route('/submit_pattern', methods=['POST'])
def submit_pattern():
    data = request.json
    pattern = data.get('pattern')
    time_taken = data.get("time_taken")
    phase = session.get('pattern_phase', 'create')
    log_time_to_csv("pattern", phase, time_taken)

    if phase == 'create':
        session['pattern'] = pattern
        session['pattern_phase'] = 'confirm'
        return jsonify({'status': 'confirm'})

    elif phase == 'confirm':
        if pattern == session.get('pattern'):
            session['pattern_phase'] = 'login'
            return jsonify({'status': 'saved', 'next': url_for('delay')})
        else:
            session['pattern_phase'] = 'create'
            return jsonify({'status': 'mismatch'})

    elif phase == 'login':
        if pattern == session.get('pattern'):
            return jsonify({'success': True, 'next': url_for('reset_pattern')})
        else:
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
            distractors = distractors[:11]
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
    log_time_to_csv("image", "login", time_taken)

    if set(attempt) == set(correct): 
        return jsonify({"success": True, "next": url_for("go_to_next")})
    return jsonify({"success": False, "message": "Incorrect images selected"})


@app.route("/submit_image_password", methods=["POST"])
def submit_image_password():
    data = request.json
    sequence = list(map(str, data.get("sequence")))# must be string!!
    time_taken = data.get("time_taken")
    phase = session.get("image_phase", "create")
    log_time_to_csv("image", phase, time_taken)

    if phase == "create":
        session["image_password"] = sequence
        session["image_phase"] = "confirm"
        return jsonify({"status": "confirm"})

    elif phase == "confirm":
        stored = session.get("image_password", [])
        if set(sequence) == set(stored): # unordered comparisons :D
            session["image_phase"] = "login"
            return jsonify({"status": "saved", "next": url_for("delay")})
        else:
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
    session.clear()
    session['visited'] = visited
    return redirect(url_for('pin'))

@app.route('/reset_pattern')
def reset_pattern():
    visited = session['visited']
    session.clear()
    session['visited'] = visited
    return redirect(url_for('pattern'))

@app.route("/reset_image_password")
def reset_image_password():
    visited = session['visited']
    session.clear()
    session['visited'] = visited
    return redirect(url_for("image_password"))


if __name__ == '__main__':
    app.run(debug=True)
    distractors = []
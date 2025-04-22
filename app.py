from flask import Flask, render_template, redirect, url_for, session, request, jsonify
import random

app = Flask(__name__)
app.secret_key = "supersecretkey"

inner_pages = {'page1', 'page2', 'page3'}
delay_pages = { 'video2.mp4', 'video2.mp4', 'video2.mp4', 'video2.mp4'}

pinLogin = ""
patternLogin = ""

ORDERED_MATCH = False

@app.route('/')
def index():
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
    # Phase can be "create" or "validate"
    phase = session.get('phase', 'create')
    return render_template('pin.html', login=(phase == 'validate'))

@app.route('/submit_pin', methods=['POST'])
def submit_pin():
    data = request.json
    pin = data.get('pin')
    print(f"PIN: {pin}")

    phase = session.get('phase', 'create')

    if phase == 'create':
        # Store and move to delay
        session['pin'] = pin
        session['phase'] = 'validate'
        session['video'] = random.choice(list(delay_pages))
        return jsonify({'next': url_for('delay')})

    elif phase == 'validate':
        if pin == session.get('pin'):
            # Clear PIN and phase after successful login
            print("Good job! Pin success :)")
            return jsonify({'success': True, 'next': url_for('go_to_next')})
        else:
            print("Sorry! Pin failure :'(")
            return jsonify({'success': False, 'error': 'Incorrect PIN'})

@app.route('/pattern')
def pattern():
    phase = session.get('phase', 'create')
    return render_template('pattern.html', login=(phase == 'validate'))

@app.route('/submit_pattern', methods=['POST'])
def submit_pattern():
    data = request.json
    pattern = data.get('pattern')
    phase = session.get('phase', 'create')

    if phase == 'create':
        session['pattern'] = pattern
        session['phase'] = 'validate'
        return jsonify({'status': 'saved', 'next': url_for('delay')})

    elif phase == 'validate':
        if pattern == session.get('pattern'):
            return jsonify({'success': True, 'next': url_for('reset_pattern')})
        else:
            return jsonify({'success': False, 'error': 'Incorrect pattern. Try again.'})

@app.route("/submit_image_login", methods=["POST"])
def submit_image_login():
    data = request.json
    attempt = data.get("sequence")
    correct = session.get("image_password", [])

    if ORDERED_MATCH:
        is_correct = attempt == correct
    else:
        is_correct = set(attempt) == set(correct)

    if is_correct:
        return jsonify({"success": True, "next": url_for("go_to_next")})
    else:
        return jsonify({"success": False, "message": "Incorrect images selected"})


@app.route("/submit_image_password", methods=["POST"])
def submit_image_password():
    data = request.json
    sequence = list(map(str, data.get("sequence")))  # make sure they're strings
    phase = session.get("phase", "create")

    if phase == "create":
        session["image_password"] = sequence
        session["phase"] = "confirm"
        return jsonify({"status": "confirm"})

    elif phase == "confirm":
        stored = session.get("image_password", [])
        if set(sequence) == set(stored):  # unordered comparison
            session["phase"] = "login"
            return jsonify({"status": "saved", "next": url_for("delay")})
        else:
            session["phase"] = "create"
            return jsonify({"status": "mismatch"})


@app.route("/image_password")
def image_password():
    phase = session.get('phase', 'create')

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
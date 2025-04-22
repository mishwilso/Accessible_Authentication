from flask import Flask, render_template, redirect, url_for, session, request, jsonify
import random

app = Flask(__name__)
app.secret_key = "supersecretkey"

inner_pages = {'page1', 'page2', 'page3'}

pinLogin = ""
patternLogin = ""

@app.route('/')
def index():
    session['visited'] = []
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


@app.route('/delay')
def delay():
    referrer = request.referrer or url_for('pin')
    return render_template('delay.html', return_url=referrer)

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

if __name__ == '__main__':
    app.run(debug=True)
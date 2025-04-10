from flask import Flask, render_template, redirect, url_for, session
import random

app = Flask(__name__)
app.secret_key = "supersecretkey"

inner_pages = {'page1', 'page2', 'page3'}

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

    return render_template(f"{page}.html")

@app.route('/done')
def done():
    return render_template('done.html')

if __name__ == '__main__':
    app.run(debug=True)
from flask import Flask, render_template, session, redirect, url_for, jsonify, request
import json
import os

app = Flask(__name__)
app.secret_key = 'dumpdumpbake2025'

# Load data
with open('data.json') as f:
    DATA = json.load(f)

# Simple single-user state (as per assignment)
user_state = {
    'started_at': None,
    'mealprep_steps_visited': [],
    'recipe_chosen': None,
    'recipe_steps_visited': {},
    'quiz_answers': {},
    'quiz_steps_visited': {},
}

def record(key, value):
    if isinstance(user_state[key], list):
        if value not in user_state[key]:
            user_state[key].append(value)
    elif isinstance(user_state[key], dict):
        user_state[key].update(value)
    else:
        user_state[key] = value

# ── Home ──────────────────────────────────────────────────────────────────────

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/start')
def start():
    import datetime
    user_state['started_at'] = str(datetime.datetime.now())
    return redirect(url_for('mealprep', step=1))

# ── Meal Prep Slides ──────────────────────────────────────────────────────────

@app.route('/mealprep/<int:step>')
def mealprep(step):
    slides = DATA['mealprep']
    total = len(slides)
    if step < 1 or step > total:
        return redirect(url_for('mealprep', step=1))

    record('mealprep_steps_visited', step)

    slide = slides[step - 1]
    prev_url = url_for('mealprep', step=step - 1) if step > 1 else None

    # Last mealprep slide → go to recipe chooser
    if step == total:
        next_url = url_for('choose_recipe')
    else:
        next_url = url_for('mealprep', step=step + 1)

    return render_template(
        'mealprep.html',
        slide=slide,
        step=step,
        total=total,
        prev_url=prev_url,
        next_url=next_url,
    )

# ── Recipe Chooser ────────────────────────────────────────────────────────────

@app.route('/choose')
def choose_recipe():
    recipes = DATA['recipes']
    return render_template('choose.html', recipes=recipes)

# ── Recipe Steps ─────────────────────────────────────────────────────────────

@app.route('/recipe/<recipe_name>/<int:step>')
def recipe(recipe_name, step):
    if recipe_name not in DATA['recipes']:
        return redirect(url_for('choose_recipe'))

    record('recipe_chosen', recipe_name)

    steps = DATA['recipes'][recipe_name]['steps']
    total = len(steps)
    if step < 1 or step > total:
        return redirect(url_for('recipe', recipe_name=recipe_name, step=1))

    if recipe_name not in user_state['recipe_steps_visited']:
        user_state['recipe_steps_visited'][recipe_name] = []
    if step not in user_state['recipe_steps_visited'][recipe_name]:
        user_state['recipe_steps_visited'][recipe_name].append(step)

    current_step = steps[step - 1]
    prev_url = url_for('recipe', recipe_name=recipe_name, step=step - 1) if step > 1 else None

    if step == total:
        next_url = url_for('quiz', recipe_name=recipe_name, step=1)
        next_label = 'Take the Quiz →'
    else:
        next_url = url_for('recipe', recipe_name=recipe_name, step=step + 1)
        next_label = 'Next →'

    return render_template(
        'recipe.html',
        recipe_name=recipe_name,
        recipe_meta=DATA['recipes'][recipe_name],
        step=current_step,
        step_num=step,
        total=total,
        prev_url=prev_url,
        next_url=next_url,
        next_label=next_label,
    )

# ── Quiz (Cooking Game) ───────────────────────────────────────────────────────

@app.route('/quiz/<recipe_name>/<int:step>')
def quiz(recipe_name, step):
    if recipe_name not in DATA['quiz']:
        return redirect(url_for('choose_recipe'))

    questions = DATA['quiz'][recipe_name]
    total = len(questions)
    if step < 1 or step > total:
        return redirect(url_for('quiz', recipe_name=recipe_name, step=1))

    if recipe_name not in user_state['quiz_steps_visited']:
        user_state['quiz_steps_visited'][recipe_name] = []
    if step not in user_state['quiz_steps_visited'][recipe_name]:
        user_state['quiz_steps_visited'][recipe_name].append(step)

    question = questions[step - 1]
    prev_url = url_for('quiz', recipe_name=recipe_name, step=step - 1) if step > 1 else None

    if step == total:
        next_url = url_for('result', recipe_name=recipe_name)
        next_label = 'Finish! →'
    else:
        next_url = url_for('quiz', recipe_name=recipe_name, step=step + 1)
        next_label = 'Next →'

    return render_template(
        'quiz.html',
        recipe_name=recipe_name,
        question=question,
        step=step,
        total=total,
        prev_url=prev_url,
        next_url=next_url,
        next_label=next_label,
    )

# ── Save quiz answer (AJAX) ───────────────────────────────────────────────────

@app.route('/quiz/<recipe_name>/<int:step>/answer', methods=['POST'])
def save_answer(recipe_name, step):
    data = request.get_json()
    key = f'{recipe_name}_step_{step}'
    user_state['quiz_answers'][key] = data
    return jsonify({'status': 'ok'})

# ── Result ────────────────────────────────────────────────────────────────────

@app.route('/result/<recipe_name>')
def result(recipe_name):
    return render_template(
        'result.html',
        recipe_name=recipe_name,
        answers=user_state['quiz_answers'],
    )

# ── Debug state (dev only) ────────────────────────────────────────────────────

@app.route('/state')
def state():
    return jsonify(user_state)

if __name__ == '__main__':
    app.run(debug=True)
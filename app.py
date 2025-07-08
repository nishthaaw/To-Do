from flask import Flask, render_template, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'super-secret-key'  # Needed for flash messages
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)

# ----- DATABASE MODEL -----
class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(100), nullable=False)
    complete = db.Column(db.Boolean, default=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    deadline = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<Task {self.id}>'

# ----- GAMIFICATION VARS -----
score = 0
level = 1
streak = 0
badges = []

# ----- HOME ROUTE -----
@app.route('/', methods=['GET', 'POST'])
def index():
    global score, level, streak, badges

    if request.method == 'POST':
        if 'content' in request.form:
            task_content = request.form['content']
            deadline_str = request.form.get('deadline')
            deadline_dt = datetime.strptime(deadline_str, '%Y-%m-%dT%H:%M') if deadline_str else None

            new_task = Todo(content=task_content, deadline=deadline_dt)
            try:
                db.session.add(new_task)
                db.session.commit()

                # Gamification points
                score += 10
                streak += 1
                if score % 50 == 0:
                    level += 1
                    flash(f'🔥 Level Up! You reached Level {level}!', 'success')
                if streak % 3 == 0:
                    badges.append(f'Streak {streak} Badge')

                flash(f'✅ Task added! +10 XP | Score: {score}', 'success')
                return redirect('/')
            except Exception as e:
                db.session.rollback()
                flash('Error adding task: ' + str(e), 'danger')
                return redirect('/')
        else:
            flash('❗ No content provided', 'warning')
            return redirect('/')

    else:
        tasks = Todo.query.order_by(Todo.date_created).all()
        return render_template(
            'index.html',
            tasks=tasks,
            score=score,
            level=level,
            streak=streak,
            badges=badges,
            datetime=datetime,
            timedelta=timedelta,
            now=datetime.utcnow()
        )

# ----- DELETE ROUTE -----
@app.route('/delete/<int:id>')
def delete(id):
    task_to_delete = Todo.query.get_or_404(id)
    try:
        db.session.delete(task_to_delete)
        db.session.commit()
        flash('🗑️ Task deleted!', 'success')
        return redirect('/')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting task: ' + str(e), 'danger')
        return redirect('/')

# ----- COMPLETE ROUTE -----
@app.route('/complete/<int:id>')
def complete(id):
    task = Todo.query.get_or_404(id)
    try:
        task.complete = not task.complete
        db.session.commit()
        flash('✅ Task marked as complete!' if task.complete else '❌ Marked as incomplete!', 'success')
        return redirect('/')
    except Exception as e:
        db.session.rollback()
        flash('Error updating task: ' + str(e), 'danger')
        return redirect('/')

# ----- UPDATE ROUTE -----
@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    task = Todo.query.get_or_404(id)
    if request.method == 'POST':
        task.content = request.form['content']
        try:
            db.session.commit()
            flash('✏️ Task updated successfully!', 'success')
            return redirect('/')
        except Exception as e:
            db.session.rollback()
            flash('Error updating task: ' + str(e), 'danger')
    return render_template('update.html', task=task)

# ----- RUN APP -----
if __name__ == '__main__':
    app.run(debug=os.environ.get("FLASK_ENV") == "development")



from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///events.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# models
class College(db.Model):
    __tablename__ = "colleges"
    college_id = db.Column(db.Integer, primary_key=True)
    college_name = db.Column(db.String(200), nullable=False)

class Student(db.Model):
    __tablename__ = "students"
    student_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), unique=True)
    college_id = db.Column(db.Integer, db.ForeignKey('colleges.college_id'))

class Event(db.Model):
    __tablename__ = "events"
    event_id = db.Column(db.Integer, primary_key=True)
    event_name = db.Column(db.String(200), nullable=False)
    event_type = db.Column(db.String(50))
    date = db.Column(db.String(20))
    college_id = db.Column(db.Integer, db.ForeignKey('colleges.college_id'))

class Registration(db.Model):
    __tablename__ = "registrations"
    reg_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.student_id'))
    event_id = db.Column(db.Integer, db.ForeignKey('events.event_id'))
    status = db.Column(db.String(20), default="registered")
    feedback = db.Column(db.Integer)

@app.route("/")
def home():
    return {"msg": "Campus Event System is running"}, 200

# add college
@app.route("/colleges", methods=["POST"])
def add_college():
    data = request.get_json()
    if not data or "college_name" not in data:
        return {"error": "college_name required"}, 400
    c = College(college_name=data["college_name"])
    db.session.add(c)
    db.session.commit()
    return {"college_id": c.college_id, "college_name": c.college_name}, 201

# add student
@app.route("/students", methods=["POST"])
def add_student():
    data = request.get_json()
    s = Student(name=data.get("name"), email=data.get("email"), college_id=data.get("college_id"))
    db.session.add(s)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}, 400
    return {"student_id": s.student_id, "name": s.name}, 201

# show all students
@app.route("/students", methods=["GET"])
def show_students():
    students = Student.query.all()
    return jsonify([{"id": s.student_id, "name": s.name, "email": s.email} for s in students])

# add event
@app.route("/events", methods=["POST"])
def add_event():
    data = request.get_json()
    e = Event(event_name=data.get("event_name"), event_type=data.get("event_type"),
              date=data.get("date"), college_id=data.get("college_id"))
    db.session.add(e)
    db.session.commit()
    return {"event_id": e.event_id, "event_name": e.event_name}, 201

# register students
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    if isinstance(data, dict):
        student_id = data.get("student_id")
        event_id = data.get("event_id")
        r = Registration.query.filter_by(student_id=student_id, event_id=event_id).first()
        if r: return {"msg": "already registered", "reg_id": r.reg_id}, 200
        r = Registration(student_id=student_id, event_id=event_id)
        db.session.add(r)
        db.session.commit()
        return {"msg": "registered", "reg_id": r.reg_id}, 201
    elif isinstance(data, list):
        out = []
        for d in data:
            s_id = d.get("student_id")
            e_id = d.get("event_id")
            r = Registration.query.filter_by(student_id=s_id, event_id=e_id).first()
            if r:
                out.append({"student_id": s_id, "event_id": e_id, "status": "already"})
            else:
                r = Registration(student_id=s_id, event_id=e_id)
                db.session.add(r)
                db.session.flush()
                out.append({"student_id": s_id, "event_id": e_id, "reg_id": r.reg_id, "status": "ok"})
        db.session.commit()
        return jsonify(out), 201
    else:
        return {"error": "wrong format"}, 400

# mark attendance
@app.route("/attendance", methods=["POST"])
def attendance():
    d = request.get_json()
    r = Registration.query.filter_by(student_id=d.get("student_id"), event_id=d.get("event_id")).first()
    if not r: return {"error": "not registered"}, 404
    r.status = "attended"
    db.session.commit()
    return {"msg": "attendance marked"}, 200

# feedback
@app.route("/feedback", methods=["POST"])
def feedback():
    d = request.get_json()
    r = Registration.query.filter_by(student_id=d.get("student_id"), event_id=d.get("event_id")).first()
    if not r: return {"error": "not registered"}, 404
    f = int(d.get("feedback"))
    if f < 1 or f > 5: return {"error": "feedback 1-5 only"}, 400
    r.feedback = f
    db.session.commit()
    return {"msg": "feedback saved"}, 200

# reports
@app.route("/reports/popularity")
def rep_pop():
    rows = db.session.execute(text("""
        SELECT e.event_id, e.event_name, COUNT(r.reg_id) as regs
        FROM events e LEFT JOIN registrations r ON e.event_id = r.event_id
        GROUP BY e.event_id ORDER BY regs DESC
    """)).fetchall()
    return jsonify([dict(r._mapping) for r in rows])

@app.route("/reports/participation")
def rep_part():
    rows = db.session.execute(text("""
        SELECT s.student_id, s.name, COUNT(r.reg_id) as attended_events
        FROM students s JOIN registrations r ON s.student_id = r.student_id
        WHERE r.status='attended'
        GROUP BY s.student_id ORDER BY attended_events DESC
    """)).fetchall()
    return jsonify([dict(r._mapping) for r in rows])

@app.route("/reports/top-students")
def rep_top():
    rows = db.session.execute(text("""
        SELECT s.student_id, s.name, COUNT(r.reg_id) as attended_events
        FROM students s JOIN registrations r ON s.student_id = r.student_id
        WHERE r.status='attended'
        GROUP BY s.student_id ORDER BY attended_events DESC LIMIT 3
    """)).fetchall()
    return jsonify([dict(r._mapping) for r in rows])

@app.route("/reports/attendance-percentage")
def rep_att():
    rows = db.session.execute(text("""
        SELECT e.event_id, e.event_name,
        SUM(CASE WHEN r.status='attended' THEN 1 ELSE 0 END)*1.0 / COUNT(r.reg_id)*100.0 as attendance_pct
        FROM events e JOIN registrations r ON e.event_id=r.event_id
        GROUP BY e.event_id
    """)).fetchall()
    return jsonify([dict(r._mapping) for r in rows])

@app.route("/reports/avg-feedback")
def rep_fb():
    rows = db.session.execute(text("""
        SELECT e.event_id, e.event_name, AVG(r.feedback) as avg_feedback
        FROM events e JOIN registrations r ON e.event_id=r.event_id
        WHERE r.feedback IS NOT NULL
        GROUP BY e.event_id
    """)).fetchall()
    return jsonify([dict(r._mapping) for r in rows])

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)

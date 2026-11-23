import os, json, sqlite3, secrets, time
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import requests

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-before-deploying")
DB_PATH = os.environ.get("DATABASE_PATH", "python_duo.db")
PISTON_URL = "https://emkc.org/api/v2/piston/execute"

PROBLEMS = [
 {"id":1,"title":"Add Two Numbers","level":"Easy","topic":"Basics","description":"Complete the function to return the sum of a and b.","function":"add_numbers","starter":"def add_numbers(a, b):\n    # Return the sum of a and b\n    pass","tests":[([2,3],5),([-4,9],5),([0,0],0)]},
 {"id":2,"title":"Even or Odd","level":"Easy","topic":"Conditionals","description":"Return the string 'Even' if n is even, otherwise return 'Odd'.","function":"even_or_odd","starter":"def even_or_odd(n):\n    # Return 'Even' or 'Odd'\n    pass","tests":[([4],"Even"),([7],"Odd"),([0],"Even")]},
 {"id":3,"title":"Find the Largest","level":"Easy","topic":"Lists","description":"Return the largest number in the given list. The list will not be empty.","function":"find_largest","starter":"def find_largest(nums):\n    # Return the largest number\n    pass","tests":[([[1,5,2]],5),([[-8,-2,-10]],-2),([[7]],7)]},
 {"id":4,"title":"Reverse a String","level":"Easy","topic":"Strings","description":"Return the given string in reverse order.","function":"reverse_string","starter":"def reverse_string(text):\n    # Return the reversed string\n    pass","tests":[(["python"],"nohtyp"),(["hello"],"olleh"),(["a"],"a")]},
 {"id":5,"title":"Count Vowels","level":"Easy","topic":"Strings","description":"Return the number of vowels (a, e, i, o, u) in the string. Treat uppercase as vowels too.","function":"count_vowels","starter":"def count_vowels(text):\n    # Count a, e, i, o, u\n    pass","tests":[(["python"],1),(["EDUCATION"],5),(["xyz"],0)]},
 {"id":6,"title":"Sum of List","level":"Easy","topic":"Loops","description":"Return the sum of all numbers in the list.","function":"sum_list","starter":"def sum_list(nums):\n    # Return the total\n    pass","tests":[([[1,2,3]],6),([[-1,5]],4),([[]],0)]},
 {"id":7,"title":"Palindrome","level":"Easy","topic":"Strings","description":"Return True if text reads the same forward and backward, otherwise False. Compare lowercase.","function":"is_palindrome","starter":"def is_palindrome(text):\n    # Return True or False\n    pass","tests":[(["madam"],True),(["Python"],False),(["Level"],True)]},
 {"id":8,"title":"Factorial","level":"Medium","topic":"Loops","description":"Return n factorial. Assume n is an integer from 0 to 10.","function":"factorial","starter":"def factorial(n):\n    # Return n factorial\n    pass","tests":[([5],120),([0],1),([3],6)]},
 {"id":9,"title":"FizzBuzz","level":"Medium","topic":"Conditionals","description":"Return 'FizzBuzz' for multiples of 3 and 5, 'Fizz' for 3, 'Buzz' for 5, otherwise the number as a string.","function":"fizz_buzz","starter":"def fizz_buzz(n):\n    # Return the correct string\n    pass","tests":[([15],"FizzBuzz"),([9],"Fizz"),([10],"Buzz"),([7],"7")]},
 {"id":10,"title":"Two Sum","level":"Medium","topic":"Lists","description":"Return the indices of two different values that add up to target. Exactly one answer exists.","function":"two_sum","starter":"def two_sum(nums, target):\n    # Return [index1, index2]\n    pass","tests":[([[2,7,11,15],9],[0,1]),([[3,2,4],6],[1,2]),([[-1,-2,-3,-4,-5],-8],[2,4])]},
]

def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con = db()
    con.execute("""CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL,
      password TEXT NOT NULL, display_name TEXT NOT NULL)""")
    con.execute("""CREATE TABLE IF NOT EXISTS submissions (
      id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
      problem_id INTEGER NOT NULL, passed INTEGER NOT NULL, total INTEGER NOT NULL,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      UNIQUE(user_id, problem_id))""")
    # Demo accounts are created from environment variables on first start.
    for username, password, display in [
      (os.environ.get("MEMBER1_USERNAME","narendra"), os.environ.get("MEMBER1_PASSWORD","ChangeMe123!"), os.environ.get("MEMBER1_NAME","Narendra")),
      (os.environ.get("MEMBER2_USERNAME","friend"), os.environ.get("MEMBER2_PASSWORD","ChangeMe456!"), os.environ.get("MEMBER2_NAME","Friend"))
    ]:
        row = con.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()
        if not row:
            con.execute("INSERT INTO users(username,password,display_name) VALUES(?,?,?)", (username,generate_password_hash(password),display))
    con.commit()
    con.close()

init_db()

def login_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if "user_id" not in session: return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapped

@app.route("/")
def home():
    return redirect(url_for("dashboard" if "user_id" in session else "login"))

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username","").strip()
        password = request.form.get("password","")
        con = db()
        user = con.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        con.close()
        if user and check_password_hash(user["password"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["display_name"] = user["display_name"]
            return redirect(url_for("dashboard"))
        flash("Username or password is incorrect.")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    con = db()
    users = con.execute("""SELECT u.id,u.display_name,COALESCE(SUM(CASE WHEN s.passed=s.total THEN 1 ELSE 0 END),0) solved,
      COALESCE(SUM(CASE WHEN s.passed=s.total THEN s.total ELSE 0 END),0) passed FROM users u LEFT JOIN submissions s ON s.user_id=u.id
      GROUP BY u.id ORDER BY solved DESC, passed DESC""").fetchall()
    mine = con.execute("SELECT problem_id FROM submissions WHERE user_id=? AND passed=total", (session["user_id"],)).fetchall()
    con.close()
    solved = {r["problem_id"] for r in mine}
    return render_template("dashboard.html", problems=PROBLEMS, users=users, solved=solved)

@app.route("/problem/<int:problem_id>")
@login_required
def problem(problem_id):
    p = next((x for x in PROBLEMS if x["id"] == problem_id), None)
    if not p: return "Problem not found", 404
    return render_template("problem.html", p=p)

@app.route("/api/run", methods=["POST"])
@login_required
def run_code():
    data = request.get_json(force=True)
    try: problem_id = int(data.get("problem_id"))
    except (TypeError, ValueError): return jsonify(error="Invalid problem."), 400
    p = next((x for x in PROBLEMS if x["id"] == problem_id), None)
    code = data.get("code","")
    if not p or not isinstance(code,str) or not code.strip() or len(code) > 12000:
        return jsonify(error="Please enter valid code (maximum 12,000 characters)."), 400
    # User code runs on the external Piston execution service, not on this web server.
    harness = "\nimport json\n_fn = " + p["function"] + "\n_cases = " + repr(p["tests"]) + "\nfor _args, _expected in _cases:\n    try:\n        _actual = _fn(*_args)\n        print(json.dumps(_actual))\n    except Exception as _e:\n        print('DUO_ERROR:' + type(_e).__name__)\n"
    try:
        response = requests.post(PISTON_URL, json={
          "language":"python","version":"3.10.0",
          "files":[{"name":"main.py","content":code + harness}],
          "stdin":"","run_timeout":3000,"compile_timeout":10000
        }, timeout=15)
        response.raise_for_status()
        result = response.json()
    except Exception:
        return jsonify(error="Code runner is temporarily unavailable. Please try again."), 502
    run = result.get("run", {})
    output = run.get("output","").splitlines()
    if run.get("code",0) != 0 and not output:
        return jsonify(error=(run.get("stderr") or "Your code could not run.")[:1000]), 200
    passed = 0
    details = []
    for i, test in enumerate(p["tests"]):
        got = output[i].strip() if i < len(output) else ""
        expected = json.dumps(test[1], separators=(",",":"))
        try:
            ok = json.loads(got) == test[1]
        except Exception:
            ok = False
        passed += int(ok)
        details.append({"number":i+1,"passed":ok,"expected":expected,"actual":got or "(no output)"})
    all_passed = passed == len(p["tests"])
    con = db()
    con.execute("""INSERT INTO submissions(user_id,problem_id,passed,total) VALUES(?,?,?,?)
      ON CONFLICT(user_id,problem_id) DO UPDATE SET passed=MAX(passed,excluded.passed), total=excluded.total""",
      (session["user_id"],problem_id,passed,len(p["tests"])))
    con.commit(); con.close()
    return jsonify(passed=passed,total=len(p["tests"]),accepted=all_passed,details=details,
                   stderr=(run.get("stderr","")[:1000] if run.get("stderr") else ""))

@app.errorhandler(500)
def server_error(e):
    return "Something went wrong. Please refresh and try again.", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)), debug=False)

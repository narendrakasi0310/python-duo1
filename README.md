# Python Duo

A small two-member online Python practice website with login, beginner challenges, test-case checking, and a shared leaderboard.

## Features
- Two separate member logins
- 10 beginner Python challenges
- Browser-based Python editor
- Run & submit against visible test cases
- Shared progress leaderboard
- SQLite database stored on a Render persistent disk

## Important security note
Python code execution is sent to the external Piston API. Do not use this starter app for public/untrusted users or sensitive code. A production-grade coding platform should use an isolated, resource-limited execution service, stronger password hashing, rate limiting, CSRF protection, and robust abuse controls. The two demo accounts use environment-configured passwords; set strong unique passwords before deployment.

## Deploy online with Render
1. Create a GitHub account and a new repository named `python-duo`.
2. Upload all files in this folder to that repository.
3. Create a Render account and choose **New → Blueprint**.
4. Connect the GitHub repository. Render reads `render.yaml`.
5. During setup, enter strong values for `MEMBER1_PASSWORD` and `MEMBER2_PASSWORD`. Keep the usernames as `narendra` and `friend`, or change them in the environment settings.
6. Deploy. Render will provide a public `https://...onrender.com` website link.
7. Share that link with your friend. Give each person their own username and password.

The included Render blueprint uses a paid persistent disk/service plan. Check Render's current pricing before deploying; free web services may sleep and do not provide persistent local disk storage.

## Run on your own computer
Requires Python 3.10+.

```bash
pip install -r requirements.txt
set MEMBER1_PASSWORD=YourStrongPassword1
set MEMBER2_PASSWORD=YourStrongPassword2
python app.py
```

Open `http://127.0.0.1:5000`.

## Add more problems
Edit the `PROBLEMS` list in `app.py`. Each problem needs:
- `id`, `title`, `level`, `topic`, `description`
- `function`: the function name the learner must define
- `starter`: starter code shown in the editor
- `tests`: list of `(arguments, expected_result)` pairs

The current test harness expects the learner's code to define the named function.

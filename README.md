# routewatch

Lightweight HTTP route coverage tracker for FastAPI and Flask apps.

---

## Installation

```bash
pip install routewatch
```

---

## Usage

`routewatch` hooks into your existing FastAPI or Flask app and tracks which routes are hit during tests or runtime, giving you a coverage report at the end.

**FastAPI example:**

```python
from fastapi import FastAPI
from routewatch import RouteWatch

app = FastAPI()
watcher = RouteWatch(app)

@app.get("/users")
def get_users():
    return {"users": []}

@app.get("/health")
def health():
    return {"status": "ok"}

# After running your tests:
watcher.report()
# ✔ /users     [HIT]
# ✘ /health    [MISSED]
# Route coverage: 50%
```

**Flask example:**

```python
from flask import Flask
from routewatch import RouteWatch

app = Flask(__name__)
watcher = RouteWatch(app)

@app.route("/ping")
def ping():
    return "pong"

watcher.report()
```

Run with your test suite to identify untested or unused endpoints before shipping.

---

## Configuration

| Option | Default | Description |
|--------|---------|-------------|
| `exclude` | `[]` | List of route patterns to ignore |
| `output` | `stdout` | Output target (`stdout` or file path) |

---

## License

MIT © routewatch contributors
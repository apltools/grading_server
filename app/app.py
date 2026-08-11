import pathlib

import schedule
import tools

import rq_dashboard
from flask import Flask, request, render_template

from helpers import InvalidRequest, form_field, json_response, requires_password, save_upload

UPLOAD_FOLDER = './uploads'
pathlib.Path(UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)

with open("/run/secrets/app_password") as f:
    PASSWORD = f.read().strip()

app = Flask(__name__)
app.config.from_object(rq_dashboard.default_settings)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024
app.config["RQ_DASHBOARD_REDIS_URL"] = "redis://redis:6379"

rq_dashboard.web.setup_rq_connection(app)
app.register_blueprint(rq_dashboard.blueprint, url_prefix="/rq")


# Every grading endpoint is protected with the one shared password
password_required = requires_password(PASSWORD)


@app.errorhandler(InvalidRequest)
def invalid_request(error):
    return str(error), 400


@app.route("/")
def index():
    return render_template("index.html", tools=tools.TOOLS.values())


def grade(tool):
    """The POST endpoint of a single grading tool."""
    @password_required
    def view():
        args = {name: form_field(name) for name in tool.fields}
        filepath = save_upload(app.config['UPLOAD_FOLDER'])
        webhook = request.form.get("webhook") or None

        job_id = scheduler.start(tool.name, args, filepath, webhook)

        return json_response(id=job_id, message="use /get/<id> to get results")
    return view


# One POST endpoint per grading tool, see tools.py
for tool in tools.TOOLS.values():
    for route in (tool.name, *tool.aliases):
        app.add_url_rule(f"/{route}", f"grade_{route}", grade(tool), methods=["POST"])


@app.route('/get/<id>', methods=["GET"])
def get(id):
    status, result = scheduler.get(id)

    if status == schedule.Status.UNKNOWN:
        return json_response(id=id, message="job is unknown", status="unknown")

    if status == schedule.Status.BUSY:
        return json_response(id=id, message="job is running", status="busy")

    if status == schedule.Status.QUEUED:
        return json_response(id=id, message=f"job is queued at position: {result}", status="queued", result=result)

    if status == schedule.Status.FAILED:
        return json_response(id=id, message="job has failed", status="failed", result=result)

    return json_response(id=id, message="job is finished", status="finished", result=result)

scheduler = schedule.Scheduler()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)

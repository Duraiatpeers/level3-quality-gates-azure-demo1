# ----------------------------------------------------------------------
# Mock deployment: no Azure App Service, nothing real is deployed
# ----------------------------------------------------------------------
# Copies the app folder into a "staging" folder and writes deployment.json (a deployment record).
# The pipeline publishes that folder as an artifact, so you can open it and see exactly what "went out".
# The point of the demo is WHEN this runs: only after both quality gates pass.
#
# Run locally (from the gates folder):  py deploy_mock.py
# ----------------------------------------------------------------------

import datetime
import json
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(HERE, "..", "app")
TARGET = os.path.join(os.environ.get("BUILD_ARTIFACTSTAGINGDIRECTORY", os.path.join(HERE, "..", "out")), "px-staging")

if os.path.exists(TARGET):
    shutil.rmtree(TARGET)
shutil.copytree(APP, TARGET, ignore=shutil.ignore_patterns("__pycache__"))

with open(os.path.join(APP, "release.json")) as file:
    release = json.load(file)

record = {
    "environment": "px-staging (mock)",
    "app_version": release["app_version"],
    "mode": release["mode"],
    "commit": os.environ.get("BUILD_SOURCEVERSION", "local")[:8],
    "build_number": os.environ.get("BUILD_BUILDNUMBER", "local"),
    "deployed_at_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
    "gates_passed": ["promptfoo", "ragas-faithfulness"],
}
with open(os.path.join(TARGET, "deployment.json"), "w") as file:
    json.dump(record, file, indent=2)

print("Deployed (mock) to staging:")
print(json.dumps(record, indent=2))

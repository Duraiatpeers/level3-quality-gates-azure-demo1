# ----------------------------------------------------------------------
# RAGAS quality gate: faithfulness (one quality dimension)
# ----------------------------------------------------------------------
# Asks the mock app each golden question, then a judge model (your Azure deployment) checks
# whether every claim in the answer is supported by the retrieved text. Score is 0 to 1.
# The average over all questions is compared with a minimum. Below the minimum = exit code 1 = the pipeline stops.
#
# Install:  py -m pip install "ragas==0.4.*" "openai>=1.109" "instructor>=1.11"
# Needs these four variables (in the pipeline they come from the variable group px-eval-secrets):
#   AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_CHAT_DEPLOYMENT, AZURE_OPENAI_API_VERSION
# Optional: RAGAS_FAITHFULNESS_MIN (default 0.80)
#
# Run locally (from the gates folder):  py ragas_gate.py
# Expect:  one line per question, the average, then GATE PASSED (exit 0) or GATE FAILED (exit 1).
# Also writes ragas_result.json and gate_summary_ragas.md (the pipeline shows the summary on the run page).
# ----------------------------------------------------------------------

import json
import os
import sys

from openai import AzureOpenAI
from ragas.llms import llm_factory
from ragas.metrics.collections import Faithfulness

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "app"))
import px_mock

MINIMUM = float(os.environ.get("RAGAS_FAITHFULNESS_MIN", "0.80"))

client = AzureOpenAI(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2025-04-01-preview"),
)
llm = llm_factory(os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT"], provider="azure", client=client, max_tokens=4096)
faithfulness = Faithfulness(llm=llm)

with open(os.path.join(HERE, "..", "tests", "golden.json")) as file:
    golden = json.load(file)

mode = px_mock.release()["mode"]
rows = []
for case in golden:
    reply = px_mock.ask(case["question"])
    score = faithfulness.score(
        user_input=case["question"], response=reply["answer"], retrieved_contexts=reply["contexts"]
    ).value
    rows.append({"question": case["question"], "score": score})
    print(f"{score:.2f}  {case['question']}")

average = sum(r["score"] for r in rows) / len(rows)
passed = average >= MINIMUM
print(f"\nAverage faithfulness {average:.2f}  (minimum {MINIMUM:.2f}, app mode: {mode})")

with open("ragas_result.json", "w") as file:
    json.dump({"metric": "faithfulness", "average": average, "minimum": MINIMUM, "passed": passed, "mode": mode, "rows": rows}, file, indent=2)

lines = ["# RAGAS gate: faithfulness", "", f"**{'PASSED' if passed else 'FAILED'}**: average {average:.2f}, minimum {MINIMUM:.2f} (app mode: {mode})", "", "| Question | Score |", "|---|---|"]
lines += [f"| {r['question']} | {r['score']:.2f} |" for r in rows]
with open("gate_summary_ragas.md", "w") as file:
    file.write("\n".join(lines) + "\n")
print("##vso[task.uploadsummary]" + os.path.abspath("gate_summary_ragas.md"))

if passed:
    print("GATE PASSED")
    sys.exit(0)
print("##vso[task.logissue type=error]RAGAS faithfulness gate failed: %.2f is below %.2f" % (average, MINIMUM))
print("GATE FAILED")
sys.exit(1)

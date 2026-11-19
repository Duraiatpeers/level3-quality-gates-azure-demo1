# Promptfoo calls this function for every test. It asks the mock app and returns just the answer text.
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app"))
import px_mock


def call_api(prompt, options, context):
    return {"output": px_mock.ask(prompt)["answer"]}

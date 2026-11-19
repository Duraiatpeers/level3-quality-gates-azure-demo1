# ----------------------------------------------------------------------
# Mock PX Service Assistant (no Azure, no web server, no model)
# ----------------------------------------------------------------------
# This stands in for the real app so the pipeline demo is quick and always repeatable.
# ask(question) returns the answer and the text that "retrieval" found, the same two things a real RAG app gives back.
#
# Which behaviour you get is set by "mode" in release.json (this is the file you edit during the demo):
#   good              = answers come straight from the retrieved text
#   wrong_fact        = the answer states a wrong number (a plain right/wrong failure, Promptfoo catches it)
#   unsupported_claim = the answer is right but adds claims that are not in the retrieved text (RAGAS faithfulness catches it)
# ----------------------------------------------------------------------

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

# Retrieval: for each question, the text the app found.
KNOWLEDGE = {
    "What is the maximum operating pressure of the PX-100?": [
        "The PX-100 has a maximum operating pressure of 10 bar.",
        "The PX-200 has a maximum operating pressure of 16 bar.",
    ],
    "How long is the warranty on the PX-200?": [
        "The PX-200 comes with a warranty of 24 months from the date of purchase.",
    ],
    "How often should the PX-100 be serviced?": [
        "The PX-100 must be serviced every 12 months by an authorised technician.",
    ],
    "What supply voltage does the PX-100 use?": [
        "The PX-100 runs on a 230 V single-phase supply.",
    ],
}

# Answers for each mode.
ANSWERS = {
    "good": {
        "What is the maximum operating pressure of the PX-100?": "The PX-100 has a maximum operating pressure of 10 bar.",
        "How long is the warranty on the PX-200?": "The PX-200 has a warranty of 24 months from the date of purchase.",
        "How often should the PX-100 be serviced?": "The PX-100 must be serviced every 12 months by an authorised technician.",
        "What supply voltage does the PX-100 use?": "The PX-100 runs on a 230 V single-phase supply.",
    },
    "wrong_fact": {
        "What is the maximum operating pressure of the PX-100?": "The PX-100 has a maximum operating pressure of 16 bar.",
        "How long is the warranty on the PX-200?": "The PX-200 has a warranty of 12 months from the date of purchase.",
        "How often should the PX-100 be serviced?": "The PX-100 must be serviced every 12 months by an authorised technician.",
        "What supply voltage does the PX-100 use?": "The PX-100 runs on a 230 V single-phase supply.",
    },
    "unsupported_claim": {
        "What is the maximum operating pressure of the PX-100?": "The PX-100 has a maximum operating pressure of 10 bar. It is certified to ISO 9001 and has been tested for 5000 hours at full load.",
        "How long is the warranty on the PX-200?": "The PX-200 has a warranty of 24 months from the date of purchase. The warranty also covers accidental damage and free replacement parts for life.",
        "How often should the PX-100 be serviced?": "The PX-100 must be serviced every 12 months by an authorised technician. Servicing at a bosch partner garage is free of charge.",
        "What supply voltage does the PX-100 use?": "The PX-100 runs on a 230 V single-phase supply. It also works on any supply voltage worldwide.",
    },
}


def release():
    with open(os.path.join(HERE, "release.json")) as file:
        return json.load(file)


def ask(question):
    mode = release()["mode"]
    return {
        "answer": ANSWERS[mode][question],
        "contexts": KNOWLEDGE[question],
    }

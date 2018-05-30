# Schedule automatic traces
SCHEDULE_TRIGGER = 'interval'
SCHEDULE_ARGS = {'seconds': 4000000000}

IMPORTANT_CIRCUITS = []
IMPORTANT_CIRCUITS_TRIGGER = 'interval'
IMPORTANT_CIRCUITS_ARGS = {'seconds': 20}

SDNTRACE_URL = 'http://localhost:8181/api/amlight/sdntrace/trace'

SLACK_CHANNEL = 'sdnlg'

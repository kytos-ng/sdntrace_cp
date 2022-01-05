# Schedule automatic traces
TRIGGER_SCHEDULE_TRACES = False
SCHEDULE_TRIGGER = 'interval'
SCHEDULE_ARGS = {'seconds': 120}

TRIGGER_IMPORTANT_CIRCUITS = False
IMPORTANT_CIRCUITS = []
IMPORTANT_CIRCUITS_TRIGGER = 'interval'
IMPORTANT_CIRCUITS_ARGS = {'seconds': 20}

SDNTRACE_URL = 'http://localhost:8181/api/amlight/sdntrace/trace'

SLACK_CHANNEL = 'of_notifications'

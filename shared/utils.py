import datetime

def get_formatted_server_time():
    """Return the current server time in a formatted string."""
    now = datetime.datetime.now()
    return now.strftime("%H:%M:%S")
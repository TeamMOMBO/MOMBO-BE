from datetime import datetime, timedelta
from dateutil import parser

def set_to_next_monday(weeks):
    current_date = datetime.now()
    three_weeks_ago = current_date - timedelta(weeks=weeks)

    days_until_monday = (7 - three_weeks_ago.weekday() + 0) % 7  
    next_monday = three_weeks_ago + timedelta(days=days_until_monday)

    return next_monday
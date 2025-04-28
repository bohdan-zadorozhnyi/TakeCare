from django import template
from datetime import datetime, timedelta
import re

register = template.Library()

@register.filter(name='add_minutes')
def add_minutes(time_str, minutes):
    """
    Add minutes to a time string in format "h:mm AM/PM"
    Example: "9:30 AM"|add_minutes:30 -> "10:00 AM"
    """
    # Regular expression to match time format like "9:30 AM"
    pattern = r'(\d+):(\d+)\s+(AM|PM)'
    match = re.match(pattern, time_str)
    
    if not match:
        return time_str
    
    hour = int(match.group(1))
    minute = int(match.group(2))
    period = match.group(3)
    
    # Convert to 24-hour format if PM
    if period == 'PM' and hour < 12:
        hour += 12
    elif period == 'AM' and hour == 12:
        hour = 0
    
    # Create a datetime object for today with the extracted time
    base_time = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    # Add the minutes
    new_time = base_time + timedelta(minutes=int(minutes))
    
    # Format back to 12-hour format
    new_hour = new_time.hour
    new_period = 'AM'
    
    if new_hour >= 12:
        new_period = 'PM'
        if new_hour > 12:
            new_hour -= 12
    elif new_hour == 0:
        new_hour = 12
    
    return f"{new_hour}:{new_time.minute:02d} {new_period}"
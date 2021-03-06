import re
import icalendar
from datetime import datetime, date
import time
import os
from event import Event
from unitname import UnitNames
from compatibility import *

desc_time_re = re.compile("are at (\S*)")
desc_room_re = re.compile("in room (\S*)")

def get_events(table_str, descriptions_str):
    """Split a table up into fields, and interpolate with descriptions."""
    # Parse the descriptions.
    descriptions = get_descriptions(descriptions_str)

    # Split into lines
    lines = map(str.strip, table_str.split('\n'))
    # Remove horizontal dividers
    lines = [line for line in lines if line.count('-') < 20]
    # Join the lines back together again (apart from the first), split at '|'s,
    # strip the whitespace, remove empty fields, and finally parse each event.
    return [Event(event_str, descriptions) 
            for event_str 
            in map(str.strip, ''.join(lines[1:]).split('|'))
            if len(event_str)]


def get_events_from_parts(parts):
    """Get all events from a list of pairs of description 
    and table strings from ARCADE
    x"""
    events = []
    # Find the descriptions and the table.
    for descriptions, table in parts:
        events += get_events(table, descriptions)
    return events


def parse_description(line):
    """Parse a single line of the description into a dict with keys
    'code', 'time', and 'room'.
    """
    line = line.rstrip('.')
    description = {"code" : line.split(' ')[0]}
    
    time_match = desc_time_re.search(line)
    if time_match:
        description["time"] = time_match.group(1)
        
    room_match = desc_room_re.search(line)
    if room_match:
        description["room"] = room_match.group(1)

    return description


def get_descriptions(descriptions_str):
    """Parse a block of descriptions into a dict with keys representing 
    the unit code, and values in the format of parse_description.
    """
    descriptions = map(parse_description,
                       filter(len,
                              map(str.strip,
                                  descriptions_str.split('\n'))))
    return dict((desc["code"], desc) for desc in descriptions)


def make_event(event, time_stamp):
    """Make an iCal event from an ARCADE event."""
    vevent = icalendar.Event()
    event.year = time_stamp.year

    vevent.add('summary', event.summary)
    vevent.add('dtstart', event.datetime_start)

    if not event.whole_day:
        vevent.add('dtend', event.datetime_end)

    if event.room: 
        vevent.add('location', event.room)

    if event.category:
        vevent.add('categories', event.category)

    if event.description:
        vevent.add('description', event.description)

    vevent.add('dtstamp', time_stamp)
    vevent["uid"] = event.uid
    return vevent

    
def make_cal(events, time_stamp):
    """Make an iCalendar object from a set of events and descriptions."""
    cal = icalendar.Calendar()
    cal.add('prodid', '-//ARCADE to iCal Converter//nixont9@cs.man.ac.uk//EN')
    cal.add('version', '2.0')
    cal.add('x-wr-timezone', "Europe/London")
    for event in events:
        cal.add_component(make_event(event, time_stamp))
    return cal

def write_cal(events, time_stamp, file_name):
    """Write a .ics file to file_name."""
    ical_string = make_cal(events, time_stamp).as_string()
    # Write the calendar to the .ics file.
    f = open(os.path.expanduser(file_name), 'wb')
    f.write(ical_string)
    f.close()
    Event.unit_names.write()


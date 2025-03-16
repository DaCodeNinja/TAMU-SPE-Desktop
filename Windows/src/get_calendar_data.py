import pandas as pd
import requests
import datetime
import time
from icalendar import Calendar
from bs4 import BeautifulSoup
import numpy as np
import pytz


def get_cal_data(url: str) -> list:
    response = requests.get(url)
    cal = Calendar.from_ical(response.content)
    tz = pytz.timezone('US/Central')
    events_dict = []
    
    for component in cal.walk():
        if component.name == "VEVENT":
            summary = component.get('summary')
            description = component.get('description')
            location = component.get('location')
            time_start_utc = component.get('dtstart').dt
            time_end_utc = component.get('dtend').dt if component.get('dtend') else time_start_utc

            # Convert date to datetime if necessary
            if isinstance(time_start_utc, datetime.date) and not isinstance(time_start_utc, datetime.datetime):
                time_start_utc = datetime.datetime.combine(time_start_utc, datetime.time(), tzinfo=pytz.UTC)
            if isinstance(time_end_utc, datetime.date) and not isinstance(time_end_utc, datetime.datetime):
                time_end_utc = datetime.datetime.combine(time_end_utc, datetime.time(), tzinfo=pytz.UTC)

            # Convert to local timezone
            time_start_local = time_start_utc.astimezone(tz)
            time_end_local = time_end_utc.astimezone(tz)

            # Only include events that end in the future
            if time_end_local >= datetime.datetime.now(tz):
                event_details = {
                    'start_time': time_start_local,
                    'end_time': time_end_local,
                    'Title': str(summary),
                    'Location': str(location),
                    'Description': description,
                    'Links': []
                }

                # Extract links from description using BeautifulSoup
                if description:
                    soup = BeautifulSoup(description, 'html.parser')
                    event_details['Links'] = [a['href'] for a in soup.find_all('a', href=True)]

                events_dict.append(event_details)

    return events_dict


def events_to_df(events: list) -> pd.DataFrame:
    df = pd.DataFrame(events)

    # Assuming 'start_time' and 'end_time' are in datetime format
    df.loc[:, 'Duration'] = df.apply(lambda row:
                              'All Day' if (row['end_time'] - row['start_time']).days == 1
                              else f'{(row["end_time"] - row["start_time"]).days} Days' if (row["end_time"] - row[
                                  "start_time"]).days > 1
                              else f'{(row["end_time"] - row["start_time"]).seconds // 3600} Hours', axis=1)

    date_format = '%m/%d/%Y'  # month-day-year
    time_format = '%I:%M %p'  # hour:minute AM/PM

    df.loc[:, 'Start Date'] = df.apply(
        lambda row: row['start_time'].strftime(date_format) if row['Duration'] == 'All Day' else row[
            'start_time'].strftime(date_format), axis=1)

    df.loc[:, 'End Date'] = df.apply(
        lambda row: row['start_time'].strftime(date_format) if row['Duration'] == 'All Day' else row[
            'end_time'].strftime(date_format), axis=1)

    df.loc[:, 'Start Time'] = df.apply(
        lambda row: '--' if row['Duration'] == 'All Day' else row['start_time'].strftime(time_format), axis=1)

    df.loc[:, 'End Time'] = df.apply(
        lambda row: '--' if row['Duration'] == 'All Day' else row['end_time'].strftime(time_format), axis=1)

    df.loc[:, 'Date(s)'] = df.apply(lambda row: str(row['Start Date']) if row['End Date'] == row['Start Date']
                                    else f"{row['Start Date']} - {row['End Date']}", axis=1)

    df.loc[:, 'Time(s)'] = df.apply(lambda row: f"{row['Start Time']} - {row['End Time']}"
                                    if row['Start Time'] != "--" else "--", axis=1)

    duration = df.pop('Duration')
    df.loc[:, 'Duration'] = duration

    description = df.pop('Description')
    df.loc[:, 'Description'] = description

    links = df.pop('Links')
    df.loc[:, 'Links'] = links

    df = df.sort_values(by='start_time').reset_index(drop=True)

    return df


def data() -> pd.DataFrame:
    ical_url = ("https://calendar.google.com/calendar/ical/plnhtuastogemqmscotaq3b9p8%40group.calendar.google.com/public/basic.ics")
    events_list = get_cal_data(ical_url)
    events_df = events_to_df(events_list)
    return events_df

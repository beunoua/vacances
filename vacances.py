
from collections import OrderedDict
import datetime
import json


class Holidays:
    """Store holiday data.

    Attributes:
        users (list[str]): each user name
        dates (dict[str]->list[date]): list of date for each user

    Args:
        dates (dict[str]->list[date]): list of date for each user
    """
    def __init__(self, dates={}, users=None):
        self.dates = dates

    @property
    def users(self):
        """Return user names."""
        return list(self.dates.keys())

    @property
    def nusers(self):
        """Return the number of users."""
        return len(self.dates)

    @classmethod
    def read(cls, path):
        """Read a holiday json file."""
        with open(path, 'rt') as f:
            data = json.load(f, object_pairs_hook=OrderedDict)

        users = {}
        for user, datestrlist in data.items():
            datelist = []
            for datestr in datestrlist:
                if '-' in datestr:
                    # date is a range.
                    datelist.extend(date_range_to_list(datestr))
                else:
                    datelist.append(str_to_date(datestr))
            users[user] = set(datelist)
        return cls(users)


def date_range_to_list(daterange):
    """Return a list of dates from a string representing a date range."""
    d1, d2 = [str_to_date(s) for s in daterange.split('-')]
    return [d1 + datetime.timedelta(days=i) for i in range((d2 - d1).days + 1)]


def str_to_date(s):
    """Return a `datetime.date` from a string."""
    day, month = s.split('/')
    return datetime.date(this_year(), int(month), int(day))


def this_year():
    """Return the year at the current date and time."""
    return datetime.datetime.today().year


WEEKDAYS = ['Lu', 'Ma', 'Me', 'Je', 'Ve', 'Sa', 'Di']
MONTHS = ['Janv', 'Févr', 'Mars', 'Avri', 'Mai', 'Juin', 'Juil', 'Août',
          'Sept', 'Octo', 'Nove', 'Déce']


class Calendar:
    def __init__(self, year, holidays):
        self.year = year
        self.holidays = holidays

    def monthrange(self, month):
        nextmonth = month % 12 + 1
        nextyear = self.year + 1 if nextmonth == 1 else self.year
        firstday = datetime.date(self.year, month, 1)
        lastday = datetime.date(nextyear, nextmonth, 1)
        return (1, (lastday - firstday).days)

    def itermonthdates(self, month):
        first, last = self.monthrange(month)
        for i in range(first, last + 1):
            yield datetime.date(self.year, month, i)

    def tohtml(self):
        def month_to_html(month):
            s = '<table>\n'
            s += '<th>{}</th>'.format(MONTHS[month - 1])
            for day in self.itermonthdates(month):
                weekday = WEEKDAYS[day.weekday()]
                d = {'day': day.day, 'weekday': weekday}
                s += '<tr><td>%(day)02d</td><td>%(weekday)s</td></tr>\n' % d
            s += '</table>\n'
            return s

        s = '<table>\n'
        s += '<tr>'
        for month in range(1, 13):
            s += '<td valign="top" align="center">{}</td>'.format(month_to_html(month))
        s += '</tr>'
        s += '</table>'
        return(s)


def main():
    h = Holidays.read('holidays.json')
    # cal = Calendar(2016, h)
    # print(cal.tohtml())



if __name__ == "__main__":
    main()


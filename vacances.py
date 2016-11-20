
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
    def __init__(self, dates={}):
        self.dates = dates

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
        return users


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




class Calendar:
    def __init__(self, year):
        self.year = year

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


        


def main():
    # import sys
    # import pprint
    # h = Holidays.read(sys.argv[1])
    # pprint.pprint(h)

    cal = Calendar(2016)
    cal.tohtml()




if __name__ == "__main__":
    main()


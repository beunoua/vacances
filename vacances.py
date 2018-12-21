
import argparse
from collections import OrderedDict
import datetime
import os.path
import sys

import jinja2
import yaml


WEEKDAYS = ['Lu', 'Ma', 'Me', 'Je', 'Ve', 'Sa', 'Di']
MONTHS = ['Janv', 'Févr', 'Mars', 'Avri', 'Mai', 'Juin', 'Juil', 'Août',
          'Sept', 'Octo', 'Nove', 'Déce']


class Holidays:
    """Store holiday data.

    Attributes:
        users (list[str]): each user name
        dates (dict[str]->list[date]): list of date for each user

    Args:
        dates (dict[str]->list[date]): list of date for each user
    """
    def __init__(self, dates={}, public=[]):
        self.dates = dates
        self.public = public

    def __str__(self):
        return str(self.dates)

    def items(self):
        return self.dates.items()

    def __getitem__(self, key):
        return self.dates[key]

    @property
    def users(self):
        """Return user names."""
        return list(self.dates.keys())

    @property
    def nusers(self):
        """Return the number of users."""
        return len(self.dates)

    @classmethod
    def read(cls, path, year):
        """Read a holiday json file."""
        with open(path, 'rt') as f:
            data = ordered_load(f)

        users = OrderedDict()
        public = []
        for user, datestrlist in data.items():
            datelist = []
            if datestrlist is not None:
                for datestr in datestrlist:
                    if '-' in datestr:
                        # date is a range.
                        datelist.extend(date_range_to_list(datestr, year))
                    else:
                        datelist.append(str_to_date(datestr, year))
            if user != 'Férié':
                users[user.lower()] = set(datelist)
            else:
                public = set(datelist)

        return cls(users, public)


class Date(datetime.date):
    def weekday_str(self):
        return WEEKDAYS[self.weekday()]

    def day_str(self):
        return '{:02d}'.format(self.day)


class Calendar:
    def __init__(self, year, holidays):
        self.year = year
        self.holidays = holidays

    @staticmethod
    def month_name(monthid):
        return MONTHS[monthid - 1]

    def monthrange(self, month):
        nextmonth = month % 12 + 1
        nextyear = self.year + 1 if nextmonth == 1 else self.year
        firstday = datetime.date(self.year, month, 1)
        lastday = datetime.date(nextyear, nextmonth, 1)
        return (1, (lastday - firstday).days)

    def itermonthdates(self, month):
        first, last = self.monthrange(month)
        for i in range(first, last + 1):
            yield Date(self.year, month, i)

    def itermonthdays(self, month):
        for date in self.itermonthdates(month):
            day = '{:02d}'.format(date.day)
            weekday = WEEKDAYS[date.weekday()]
            yield day, weekday

    def tohtml(self):
        template_loader = jinja2.FileSystemLoader(searchpath='templates')
        template_env = jinja2.Environment(loader=template_loader)
        template = template_env.get_template('template.html')
        return template.render(calendar=self)


def ordered_load(stream, Loader=yaml.Loader, object_pairs_hook=OrderedDict):
    class OrderedLoader(Loader):
        pass
    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))
    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)
    return yaml.load(stream, OrderedLoader)


def date_range_to_list(daterange, year):
    """Return a list of dates from a string representing a date range."""
    d1, d2 = [str_to_date(s, year) for s in daterange.split('-')]
    return [d1 + datetime.timedelta(days=i) for i in range((d2 - d1).days + 1)]


def str_to_date(s, year):
    """Return a `datetime.date` from a string."""
    tokens = s.split('/')
    if len(tokens) == 2:
        day, month = tokens
    elif len(tokens) == 3:
        day, month, year = tokens
        if len(year) == 2:
            year = '20{}'.format(year)
    else:
        raise ValueError("Invalid date string: '{}'".format(s))
    return datetime.date(int(year), int(month), int(day))


def write_html(html, path):
    """Write html to file."""
    with open(path, 'wt') as f:
        print(html, file=f)
    print("Wrote output html to {}".format(path), file=sys.stderr)


def write_pdf(html, path):
    """Write html to pdf using pdfkit."""
    import pdfkit
    import re

    # Remove footer that contains the download to pdf link.
    regex = re.compile('(<footer>.*</footer>)', re.S|re.M)
    match = regex.search(html)
    if match:
        html = html.replace(match.group(1), '')

    # Generate PDF.
    options = {
        'page-size': 'A4',
        'encoding': 'UTF8',
        'orientation': 'Landscape',
        'dpi': 300,
        'background': '',
        'zoom': 2.4,
        'quiet': ''
    }

    pdfkit.from_string(html, path, options=options)
    print("Wrote output html to {}".format(path), file=sys.stderr)


def tail(s):
    print('\n'.join(s.splitlines()[-10:]))


def parse_command_line():
    def this_year():
        """Return the year at the current date and time."""
        return datetime.datetime.today().year

    def guess_year(args):
        basename, ext = os.path.splitext(os.path.basename(os.path.realpath(args.holidays)))
        tokens = basename.split('_')
        if len(tokens) == 2:
            try:
                return int(tokens[1])
            except:
                pass
        return this_year()

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('holidays', nargs='?', default='holidays.yaml',
                        help="Holidays file (YAML)")
    parser.add_argument('-y', '--year', default=None, type=int,
                        help="Year")
    args = parser.parse_args()
    args.year = guess_year(args)
    return args
    

def number_days_off(dates, public):
    s = 0
    for date in dates:
        if date.weekday() not in (5, 6) and date not in public:
            s += 1
    return s


def number_days_off2(dates, public):
    off = [d for d in dates if d.weekday() not in (5, 6) and d not in public]
    return len(off)


def main():
    args = parse_command_line()

    h = Holidays.read(args.holidays, args.year)

    print("Number off days off:")
    for user, dates in h.dates.items():
        print("  {:10s}  {:>3d}".format(user, number_days_off(dates, h.public)))

    cal = Calendar(args.year, h)
    html = cal.tohtml()

    write_html(html, 'index.html')
    write_pdf(html, 'calendrier_vacances.pdf')


if __name__ == "__main__":
    main()


# import timeit

# args = parse_command_line()
# h = Holidays.read(args.holidays, args.year)
# dates = h.dates['benoist']
# public = h.public

# print(timeit.timeit("number_days_off(dates, public)", number=100000, globals=globals()))
# print(timeit.timeit("number_days_off2(dates, public)", number=100000, globals=globals()))



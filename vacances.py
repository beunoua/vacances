"""Creates the holidays/care calendar."""

import argparse
import calendar
from collections import OrderedDict
import datetime
import os.path
import sys

import jinja2
import yaml


WEEKDAYS = ["Lu", "Ma", "Me", "Je", "Ve", "Sa", "Di"]
MONTHS = ["Janv", "Févr", "Mars", "Avri", "Mai", "Juin", "Juil", "Août",
          "Sept", "Octo", "Nove", "Déce"]


class Date(datetime.date):
    """A simple date class with additional helper methods."""

    @classmethod
    def from_date(cls, date):
        return cls(date.year, date.month, date.day)

    def weekday_str(self):
        """Returns a string corresponding to the week day."""
        return WEEKDAYS[self.weekday()]

    def day_str(self):
        """Returns the date zero-padded day number."""
        return f"{self.day:02d}"
    
    def is_weekend(self):
        return self.weekday() > 4
    
    def is_sunday(self):
        return self.weekday() == 6


class DateCollection:
    """Stores ensembles of dates.

    Ensembles are grouped by user.

    Attributes:
        dates (dict[str]->list[date]): list of date for each user

    Args:
        dates (dict[str]->list[date]): list of date for each user
    """
    def __init__(self, dates=None):
        if dates is None:
            dates = {}
        self.dates = dates

    def __str__(self):
        return str(self.dates)

    def items(self):
        """Iterates over dates."""
        return self.dates.items()

    def __getitem__(self, key):
        return self.dates[key]

    def date_is_free(self, date):
        """Returns True if a date is not defined in a user date list."""
        for dates in self.dates.values():
            if date in dates:
                return False
        return True
    
    def date_is_free_weekend(self, date):
        """Returns is free and is a weekend."""
        return date.is_weekend() and self.date_is_free(date)

    @property
    def users(self):
        """Returns user names."""
        return list(self.dates.keys())

    @property
    def nusers(self):
        """Returns the number of users."""
        return len(self.dates)

    def append(self, user, date):
        """Add a date to a user date list."""
        self.dates[user] |= {date}


class Holidays(DateCollection):
    """Store holidays.

    Basically a DateCollection with special "public" attribute for
    public holidays ("férié").
    """
    def __init__(self, dates=None):
        super().__init__(dates)
        self.public = self.dates.pop("férié", {})


class Care(DateCollection):
    """Store child care dates.

    Basically a DateCollection with a special method that guesses the care
    method according to the week number.
    """
    def guess_care_weeks(self, start=None, first_care=""):
        """Guesses care method according to week number.

        Args:
            start (datetime.date): date at which child care starts.
            first_care (str): user who starts the child care.
        """
        if first_care:
            assert first_care in self.dates
        else:
            first_care = list(self.dates.keys())[0]

        cal = calendar.Calendar()

        # Reorders users so that the first_care comes first.
        order = [self.users.index(first_care)]
        for i in range(len(self.users)):
            if i not in order:
                order.append(i)
        users = [self.users[i] for i in order]

        first_weekid = weekid(start)
        week_counter = 0

        for current_month in range(start.month, 13):
        #     if current_month in (3, 4):
        #           for date in cal.itermonthdates(start.year, current_month):
        #               print(date)  
        #     print("-" * 30)
        # exit()
            for date in cal.itermonthdates(start.year, current_month):
                if date.month == current_month:
                    date = Date.from_date(date)
                    if date >= start and self.date_is_free_weekend(date):
                        mod = week_counter % self.nusers
                        self.append(users[mod], date)
                    if date.is_sunday():
                        week_counter += 1


class Calendar:
    """A calendar to be rendered in as HTML."""
    def __init__(self, year, holidays, care, comments=None):
        self.year = year
        self.holidays = holidays
        self.care = care
        self.comments = comments

    @staticmethod
    def month_name(monthid):
        """Returns a month name."""
        return MONTHS[monthid - 1]

    def monthrange(self, month):
        """Returns a tuple (1, <last_day_of_the_month>)."""
        nextmonth = month % 12 + 1
        nextyear = self.year + 1 if nextmonth == 1 else self.year
        firstday = datetime.date(self.year, month, 1)
        lastday = datetime.date(nextyear, nextmonth, 1)
        return (1, (lastday - firstday).days)

    def itermonthdates(self, month):
        """Iterates over a month dates."""
        first, last = self.monthrange(month)
        for i in range(first, last + 1):
            yield Date(self.year, month, i)

    def itermonthdays(self, month):
        """Iterates over a month days.

        Yields:
            (str, str): zero-padded day number, day name
        """
        for date in self.itermonthdates(month):
            day = f"{date.day:02d}"
            weekday = WEEKDAYS[date.weekday()]
            yield day, weekday

    def tohtml(self):
        """Renders calendar to HTML."""
        template_loader = jinja2.FileSystemLoader(searchpath="templates")
        template_env = jinja2.Environment(loader=template_loader)
        template = template_env.get_template("template.html")
        return template.render(calendar=self)


def weekid(date):
    """Returns the date week id."""
    return date.isocalendar()[1]


def read_date_yaml(path, year):
    """Reads a yaml file containing users and date ranges for each user."""
    with open(path, "rt") as f:
        data = ordered_load(f)

    users = OrderedDict()
    for user, datestrlist in data.items():
        datelist = []
        if datestrlist is not None:
            for datestr in datestrlist:
                if datestr is None:
                    raise ValueError(f"user: {user}: empty date string")
                if "-" in datestr:
                    # date is a range.
                    datelist.extend(date_range_to_list(datestr, year))
                else:
                    datelist.append(str_to_date(datestr, year))
        users[user.lower()] = set(datelist)

    return users


def ordered_load(stream, Loader=yaml.Loader, object_pairs_hook=OrderedDict):
    """Loads a YAML file in an orderly fashion."""
    class OrderedLoader(Loader):
        """Dummy Loader used for ordered load."""

    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))

    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)
    return yaml.load(stream, OrderedLoader)


def date_range_to_list(daterange, year):
    """Returns a list of dates from a string representing a date range."""
    start, end = [str_to_date(s, year) for s in daterange.split("-")]
    return [start + datetime.timedelta(days=i)
            for i in range((end - start).days + 1)]


def str_to_date(date_string, year):
    """Returns a `datetime.date` from a string."""
    tokens = date_string.split("/")
    if len(tokens) == 2:
        day, month = tokens
    elif len(tokens) == 3:
        day, month, year = tokens
        if len(year) == 2:
            year = "20{}".format(year)
    else:
        raise ValueError("Invalid date string: '{}'".format(date_string))
    try:
        return datetime.date(int(year), int(month), int(day))
    except ValueError as exc:
        raise ValueError(f"day is out of range: {year}/{month}/{day}") from exc


def write_html(html, path):
    """Writes html to file."""
    with open(path, "wt") as f:
        print(html, file=f)
    print("Wrote output html to {}".format(path), file=sys.stderr)


def write_pdf(html, path, zoom):
    """Writes html to pdf using pdfkit."""
    import pdfkit
    import re

    # Remove footer that contains the download to pdf link.
    regex = re.compile("(<footer>.*</footer>)", re.S|re.M)
    match = regex.search(html)
    if match:
        html = html.replace(match.group(1), "")

    # Generate PDF.
    options = {
        "page-size": "A4",
        "encoding": "UTF8",
        "orientation": "Landscape",
        "dpi": 300,
        "background": "",
        "zoom": zoom,
        "quiet": ""
    }

    pdfkit.from_string(html, path, options=options)
    print(f"Wrote output pdf to {path}", file=sys.stderr)


def this_year():
    """Returns the year at the current date and time."""
    return datetime.datetime.today().year


def is_date(date_string):
    """Converts a date string to a date.

    Args:
        date_string (str): date string in the format yyyy-mm-dd

    Returns:
        datetime.Date
    """
    year, month, day = [int(token) for token in date_string.split("-")]
    return datetime.date(year, month, day)


def parse_command_line():
    """Command-line parsing."""
    def guess_year(args):
        basename = os.path.splitext(os.path.basename(os.path.realpath(args.holidays)))[0]
        tokens = basename.split("_")
        if len(tokens) == 2:
            try:
                return int(tokens[1])
            except Exception:
                pass
        return this_year()

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("holidays", nargs="?", default="holidays.yaml",
                        help="Holidays file (YAML)")
    parser.add_argument("care", nargs="?", default="care.yaml",
                         help="children care file (YAML)")
    parser.add_argument("-y", "--year", default=None, type=int,
                        help="Year")
    parser.add_argument("--care-start", type=is_date,
                        help="date when child care starts")
    parser.add_argument("--first-care",
                        help="first parent to start child care")
    parser.add_argument("--no-pdf", action="store_true",
                        help="no PDF rendering")
    parser.add_argument("--pdf-zoom", type=float, default=2.,
                        help="zoom factor for PDF rendering")
    parser.add_argument("-c", "--comments",
                        help="commentary file")
    parser.add_argument("--output-dir", default=".",
                        help="output directory for index.html and calendrier_vacances.pdf")
    args = parser.parse_args()
    args.year = guess_year(args)
    return args


def read_comments(path):
    """Reads comment file."""
    with open(path, "rt") as fp:
        return fp.read()


def main():
    args = parse_command_line()

    # Check output directory exists (and is a directory).
    if not os.path.isdir(args.output_dir):
        raise NotADirectoryError("invalid output directory "
                                 f"'{args.output_dir}'")

    output_html = os.path.join(args.output_dir, "index.html")
    output_pdf = os.path.join(args.output_dir, "calendrier_vacances.pdf")

    # Default care start to January 1st unless specified.
    care_start = args.care_start
    if not care_start:
        care_start = is_date(f"{args.year}-01-01")

    # Reads care.
    care = Care(read_date_yaml(args.care, args.year))
    first_care = args.first_care
    if not first_care:
        first_care = care.users[0]
    else:
        assert first_care in care.users
    care.guess_care_weeks(start=care_start, first_care=first_care)

    # Reads holidays.
    holidays = Holidays(read_date_yaml(args.holidays, args.year))

    # Reads comments.
    comments = read_comments(args.comments) if args.comments else None
    
    # Calendar creation.
    cal = Calendar(args.year, holidays, care, comments)
    html = cal.tohtml()

    # Calendar output.
    write_html(html, output_html)
    if not args.no_pdf:
        write_pdf(html, output_pdf, args.pdf_zoom)


if __name__ == "__main__":
    main()

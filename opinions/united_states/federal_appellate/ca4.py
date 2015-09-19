from juriscraper.AbstractSite import logger
from juriscraper.OpinionSite import OpinionSite
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil.rrule import rrule, DAILY


class Site(OpinionSite):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://pacer.ca4.uscourts.gov/cgi-bin/opinions.pl'
        self.court_id = self.__module__
        td = date.today()
        self.interval = 30
        self.parameters = {'CASENUM': '',
                           'FROMDATE': (td - timedelta(days=10)).strftime('%m-%d-%Y'),
                           'TITLE': '',
                           'TODATE': td.strftime('%m-%d-%Y')}
        self.method = 'POST'

        self.back_scrape_iterable = [i.date() for i in rrule(
            DAILY,
            interval=self.interval,  # Every interval days
            dtstart=date(1996, 1, 1),
            until=date(2015, 1, 1),
        )]

    def _get_case_names(self):
        path = '//tr/td[4]/text()'
        names = []
        for s in self.html.xpath(path):
            if s.strip():
                names.append(s)
        logger.info(str(len(names)))
        return names

    def _get_download_urls(self):
        path = '//tr/td[1]/a/@href'
        return list(self.html.xpath(path))

    def _get_case_dates(self):
        path = '//tr/td[3]/text()'
        return [datetime.strptime(date_string.strip(), '%Y/%m/%d').date()
                for date_string in self.html.xpath(path)]

    def _get_docket_numbers(self):
        path = '//tr/td[2]//text()'
        docket_numbers = []
        for s in self.html.xpath(path):
            if s.strip():
                docket_numbers.append(s)
        return docket_numbers

    def _get_precedential_statuses(self):
        statuses = []
        # using download link, we can get the statuses
        for download_url in self.download_urls:
            file_name = download_url.split('/')[-1]
            if 'u' in file_name.lower():
                statuses.append('Unpublished')
            else:
                statuses.append('Published')
        return statuses

    def _download_backwards(self, d):

        self.parameters = {
            'CASENUM': '',
            'FROMDATE': d.strftime('%m-%d-%Y'),
            'TITLE': '',
            'TODATE': (d + timedelta(self.interval)).strftime('%m-%d-%Y')
        }

        self.html = self._download()
        if self.html is not None:
            # Setting status is important because it prevents the download
            # function from being run a second time by the parse method.
            self.status = 200

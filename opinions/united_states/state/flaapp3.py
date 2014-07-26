#  Scraper for Florida 3rd District Court of Appeal
# CourtID: flaapp3
# Court Short Name: flaapp3
# Author: Andrei Chelaru
# Reviewer:
# Date created: 21 July 2014


from datetime import date
import re
import time
import requests
from lxml import html

from juriscraper.OpinionSite import OpinionSite
from juriscraper.opinions.united_states.state import fla


class Site(fla.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        self.url = 'http://www.3dca.flcourts.org/Opinions/ArchivedOpinions.shtml'
        self.base_path = "//h3/following::text()[.='OPINIONS']/following::table[1]//tr"

    def _download(self, request_dict={}):
        html_l = OpinionSite._download(self)
        s = requests.session()
        html_trees = []
        # this path reads the row for the last month in that year
        path = "//th[contains(., '{year}')]/following::tr[1]/td[position()>1]/a[contains(., '/')]/@href".format(
            year=self.year
        )
        # to get all the dates in that page the following path can be used:
        # path = "//th/following::tr/td[position()>1]/a[contains(., '/')]/@href"
        for url in html_l.xpath(path):
            r = s.get(url,
                      headers={'User-Agent': 'Juriscraper'},
                      **request_dict)
            r.raise_for_status()

            # If the encoding is iso-8859-1, switch it to cp1252 (a superset)
            if r.encoding == 'ISO-8859-1':
                r.encoding = 'cp1252'

            # Grab the content
            text = self._clean_text(r.text)
            html_tree = html.fromstring(text)
            html_tree.make_links_absolute(self.url)

            remove_anchors = lambda url: url.split('#')[0]
            html_tree.rewrite_links(remove_anchors)
            html_trees.append(html_tree)
        return html_trees

    def _get_case_names(self):
        case_names = []
        for html_tree in self.html:
            case_names.extend(self._return_case_names(html_tree))
        return case_names

    def _return_case_names(self, html_tree):
        path = "{base}/td[2]//text()".format(base=self.base_path)
        return list(html_tree.xpath(path))

    def _get_download_urls(self):
        download_urls = []
        for html_tree in self.html:
            download_urls.extend(self._return_download_urls(html_tree))
        return download_urls

    def _return_download_urls(self, html_tree):
        path = "{base}/td[1]//a/@href".format(base=self.base_path)
        return list(html_tree.xpath(path))

    def _get_case_dates(self):
        case_dates = []
        for html_tree in self.html:
            case_dates.extend(self._return_dates(html_tree))
        return case_dates

    def _return_dates(self, html_tree):
        path = "//h3/text()"
        dates = []
        text = html_tree.xpath(path)[0]
        text = re.search('(\d{2}-\d{2}-\d{4})', text).group(1)
        case_date = date.fromtimestamp(time.mktime(time.strptime(text.strip(), '%m-%d-%Y')))
        dates.extend([case_date] * int(html_tree.xpath("count({base})".format(base=self.base_path))))
        return dates

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_dates)

    def _get_docket_numbers(self):
        docket_numbers = []
        for html_tree in self.html:
            docket_numbers.extend(self._return_docket_numbers(html_tree))
        return docket_numbers

    def _return_docket_numbers(self, html_tree):
        path = "{base}/td[1]//a/text()".format(base=self.base_path)
        return list(html_tree.xpath(path))
#! /usr/bin/env python3
"""
WikiRacer is a program to find path between two pages
in Wikipedia. WikiRacer makes use of BFS(Breadth First
Search) for finding path between start url and end url.
"""
import argparse
import json
import logging
import re
import sys

from collections import OrderedDict
from multiprocessing import cpu_count
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from concurrent.futures import ProcessPoolExecutor, as_completed

log = logging.getLogger(__name__)

WIKIPEDIA_EN_BASE_URL = 'https://en.wikipedia.org'
WIKIPEDIA_API_URL = 'https://en.wikipedia.org/w/api.php?'


class WikiRacer:

    def __init__(self):
        # Cache to hold links for node(page title)
        self.link_cache = {}
        # All paths found by BFS
        self.paths = []
        # Wikipedia API client
        self.wiki_api_client = WikiApi()

    def _fetch_links_for_nodes(self, nodes):
        """
        Executes wiki api to fetch all links
        parallely for nodes(page titles)
        """
        # Create process pool(multiprocessing avoids python GIL)
        # with as many processes as cpu cores
        with ProcessPoolExecutor(max_workers=cpu_count()) as executor:
            # Dictonary for storing future objects return by executor
            futures = {}

            # For each node(page title) if the node is not already cached
            # submit job to executor to fetch links
            for node in nodes:
                if not self.link_cache.get(node):
                    futures[executor.submit(
                        self.wiki_api_client.fetch_page_links, node)] = node

            # 'as_completed' returns the result of each future
            # as and when it is completed
            for future in as_completed(futures):
                try:
                    # Fetch the result of future and update cache
                    links = future.result()
                    self.link_cache[node] = links
                except Exception as e:
                    self.link_cache[node] = []
                    log.error(e.reason)
        # Shutdown the executor once all jobs are completed
        executor.shutdown(wait=True)

    def _find_path_to_destination(self, page_title, end_title, path):
        """
        Determines if page title is the final destination and
        the path formed does not already exist.
        """
        if page_title == end_title:
            newpath = path + [page_title]
            if newpath not in self.paths:
                self.paths.append(newpath)
                return newpath
        # Path not found
        return False

    def bfs(self, start_title, end_title):
        """
        Finds all paths(provided there is 'sufficient' memory) between
        start page and end page by returning a generator object.

        :param start_tile: Start wikipedia page title
        :param end_title: End wikipedia page title

        :rtype list(str)(Generator)
        """
        # Queue which holds tuple of the starting page title and path formed
        queue = [(start_title, [start_title])]

        # While queue is not empty perfrom BFS on popped node from queue
        while queue:
            vertex, path = queue.pop(0)

            # Fetch all links of nodes(page titles) parallely
            self._fetch_links_for_nodes(path)

            # For each node in path get all the links on page and
            # compare against destination page title
            for node in set(path) - set(vertex):
                # Fetch links for page title from cache
                links = self.link_cache[node]
                # Iterate over links and find destination
                for page_title in links:
                    wpath = self._find_path_to_destination(
                                page_title, end_title, path
                            )
                    # If path has been found yield to caller
                    # else append path found till now to queue
                    if wpath:
                        yield wpath
                    else:
                        queue.append((page_title, path + [page_title]))


class WikiApi:

    def fetch_page_links(self, page_title,
                         format='json', limit=500,
                         title_filter='(Category:|Template:|Template_talk:)'):
        """
        Fetches all links in wikepdia page and return the same.

        :param page_title: Page title of Wikipedia page
        :param format: (optional) Format of data requested
        :param limit: (optional) Number of links requested from page
        :param title_filter: (optional) Regex for filtering page title with
                             keywords

        :rtype list of str
        """
        page_links = []
        # API params for fetching wikipedia page links
        params = urlencode({'action': 'query',
                            'prop': 'links',
                            'titles': page_title,
                            'pllimit': limit,
                            'format': format})
        url = WIKIPEDIA_API_URL + params

        # Run query by opening the api url to fetch links
        try:
            page = urlopen(url)
        except (URLError, HTTPError) as e:
            log.error(url + ": %s" % e.reason)
            return []

        # Read the results of query api and decode to utf-8
        try:
            json_data = page.read().decode('utf-8')
        except UnicodeError as e:
            log.error("UnicodeError: %s" % e)
            json_data = []

        if not json_data:
            return []

        # Convert str json data to python dict
        try:
            links = json.loads(json_data)
        except json.JSONDecodeError as e:
            log.error("Failure while trying to parse result from wiki api")
            log.error("JSONDecodeError: %s" % e)
            return []

        # From the result collect only the page title after applying
        # title_filter
        for pageid in links['query']['pages']:
            if links['query']['pages'][pageid].get('links'):
                for link in links['query']['pages'][pageid]['links']:
                    page_title = link['title'].replace(' ', '_')
                    if not re.search(title_filter, page_title):
                        page_links.append(page_title)

        return page_links


def main():
    parser = argparse.ArgumentParser(description="WikiRacer")
    parser.add_argument('input_urls', help="Start and end url"
                                           " in json format string ")
    args = parser.parse_args()

    # Convert input string to json
    try:
        input_urls = json.loads(args.input_urls)
    except json.JSONDecodeError as e:
        log.error("Invalid input. Pleae check start & end urls.")
        log.error("JSONDecodeError: %s" % e)
        sys.exit(-1)

    # Get page title from url provided by user
    start_page_title = input_urls['start'].split('/')[-1]
    end_page_title = input_urls['end'].split('/')[-1]

    # Create WikiRacer object to find path between start and end url
    wikiracer = WikiRacer()

    # Perform BFS between start page and end page
    bfs_gen = wikiracer.bfs(start_page_title, end_page_title)

    # Get first path between start page and end page
    path = [WIKIPEDIA_EN_BASE_URL + '/' + node for node in next(bfs_gen)]

    # Build json output
    json_output = OrderedDict()
    json_output["start"] = input_urls["start"]
    json_output["end"] = input_urls["end"]
    json_output["path"] = path

    print(json.dumps(json_output, indent=4))


if __name__ == '__main__':
    main()

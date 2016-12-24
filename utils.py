# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""Utils to get data from PyPI, GitHub, etc."""

import json
import re
import xmlrpc

import caniusepython3
import diskcache
import lxml.html
import requests

PYPI_URL = 'https://pypi.python.org/pypi'
GITHUB_URL = 'https://github.com'
OVERRIDE_PATH = 'overrides.json'
CACHE_PATH = 'cache.data'


def get_overrides(path):
    """Load overrides from json file."""
    with open(path) as infile:
        packages = json.load(infile)
    return packages


def check_overrides(name, overrides):
    """Check whether a package has been manually overridden.

    :param name: the package name
    :param overrides: the override dictionary
    """

    if overrides is None:
        return None

    if name in overrides:
        return overrides[name]

    # no need to list packages that contain only static files
    if name.startswith('XStatic'):
        return []

    return None


def get_cache(path):
    """Get cache dictionary"""
    return diskcache.Cache(path)


def get_github_stars(user, name):
    """Crawl GitHub to obtain stars of a given repository.

    :param user: username
    :param name: name of the repository
    """
    url = '{}/{}/{}'.format(GITHUB_URL, user, name)
    response = requests.get(url)
    if response.status_code == 200:
        tree = lxml.html.fromstring(response.content)
        stars = tree.xpath('//a[@href="/{}/{}/stargazers"]/text()'.format(
            user, name))
        if stars:
            return int(stars[0].strip().replace(',', ''))
        else:
            return None
    else:
        return None


def get_top_packages():
    """Get top packages from PyPI"""
    client = xmlrpc.client.ServerProxy(PYPI_URL)
    for name, downloads in client.top_packages():
        yield {'name': name, 'downloads': downloads}


GITHUB_PATTERN = re.compile(r'https?://github.com/([^/]+)/([A-Za-z0-9_.-]+)')


def get_github_info(package_name, package_info):
    """Get GitHub info from package name."""

    # check if homepage is a GitHub repository
    home_page = package_info['info']['home_page']
    if home_page:
        matched = GITHUB_PATTERN.match(home_page)

        if matched:
            return matched.groups()

    else:
        desc = package_info['info']['description']
        if desc:
            for user, name in GITHUB_PATTERN.findall(desc):
                if name == package_name:
                    return user, name
    return None, None


def get_package_info(package_name, session):
    """Fetch package information from PyPI."""
    url = '{}/{}/json'.format(PYPI_URL, package_name)
    response = session.get(url)
    if response.status_code == 200:
        return response.json()

    return None


def get_github_packages(packages_with_info, cache=None):
    """Get packages that have GitHub repositories.

    :param packages_with_info: an iterable of packages with package_info
    """

    # create a temporary cache that discards all info
    if cache is None:
        cache = {}

    for package, package_info in packages_with_info:
        # process only if it does not already have GitHub info
        if 'github_user' not in package:
            user, name = get_github_info(package['name'], package_info)
        else:
            user, name = package['github_user'], package['github_name']

        if user and name:
            # store GitHub info
            url = 'https://github.com/{}/{}'.format(user, name)
            cache[package['name']] = (user, name, url)

            stars = get_github_stars(user, name)
            if stars is not None:
                package_with_github = {
                    'name': package['name'],
                    'downloads': package['downloads'],
                    'github_user': user,
                    'github_name': name,
                    'stars': stars,
                    'url': url,
                }

                yield package_with_github


def is_python3_enabled(package_info):
    """Check if a package is Python 3 enabled by released data."""
    releases = package_info['releases']
    for versions in releases.values():
        for version in versions:
            python_version = version['python_version']
            if python_version == 'py2.py3' or python_version.startswith('3.'):
                return True
    return False


def get_py2_packages(packages, cache=None, overrides=None):
    """Get Python 2 only packages from package list

    :param packages: an iterable of packages
    :param cache: the cache dictionary to store package info
    """

    # create a temporary cache that discards all info
    if cache is None:
        cache = {}

    session = requests.Session()
    for package in packages:
        name = package['name']

        # check if overridden as Python 3
        override_status = check_overrides(name, overrides=overrides)
        if override_status is None:
            # check if cached as Python 3
            override_status = cache.get(name)

        if override_status is not None:
            # only yield Python 2 packages
            if len(override_status) == 3:
                github_user, github_name, url = override_status
                downloads = package['downloads']

                package_with_github = {
                    'name': name,
                    'downloads': downloads,
                    'github_user': github_user,
                    'github_name': github_name,
                    'url': url,
                }
                yield (package_with_github, None)

        else:
            if caniusepython3.check(projects=[name]):
                cache[name] = ()
                continue

            package_info = get_package_info(name, session)
            if is_python3_enabled(package_info):
                cache[name] = ()
                continue

            yield (package, package_info)

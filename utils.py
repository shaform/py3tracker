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

import json
import os
import re
import xmlrpc

import caniusepython3
import lxml.html
import requests

PYPI_URL = 'https://pypi.python.org/pypi'
GITHUB_URL = 'https://github.com'
OVERRIDE_PATH = 'overrides.json'
CACHE_PATH = 'cache.data'


def get_overrides():
    with open(OVERRIDE_PATH) as f:
        packages = json.load(f)
    return packages


def check_overrides(name, overrides=get_overrides()):
    if name in overrides:
        return overrides[name]

    if name.startswith('XStatic'):
        return []

    return None


def get_cache():
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH) as f:
            cache = {l.strip(): [] for l in f}
    else:
        cache = {}
    return cache


def check_cache(name, cache=get_cache()):
    if name in cache:
        return cache[name]

    return None


def write_cache(name):
    with open(CACHE_PATH, 'a') as f:
        f.write(name + '\n')


def get_github_stars(user, name):
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
    client = xmlrpc.client.ServerProxy(PYPI_URL)
    for name, downloads in client.top_packages():
        yield {'name': name, 'downloads': downloads}


def get_github_packages(packages, check_python2=True):
    session = requests.Session()
    github_pattern = re.compile(
        r'https?://github.com/([^/]+)/([A-Za-z0-9_.-]+)')

    for package in packages:
        if 'github_user' not in package:
            url = '{}/{}/json'.format(PYPI_URL, package['name'])
            response = session.get(url)
            if response.status_code == 200:
                # check github
                package_info = response.json()
                home_page = package_info['info']['home_page']
                desc = package_info['info']['description']

                if home_page:
                    m = github_pattern.match(home_page)
                else:
                    m = None

                if m:
                    user, name = m.groups()
                    package['github_user'] = user
                    package['github_name'] = name

                elif desc:
                    package_name = package['name']
                    for user, name in github_pattern.findall(desc):
                        if name == package_name:
                            package['github_user'] = user
                            package['github_name'] = name
                            break

        if 'github_user' in package:
            # only keep Python 2 versions
            if check_python2:
                skip = False
                releases = package_info['releases']
                for versions in releases.values():
                    for version in versions:
                        python_version = version['python_version']
                        if python_version == 'py2.py3' or python_version.startswith(
                                '3.'):
                            skip = True
                            break
                    if skip:
                        break

                if skip:
                    continue

            # get stars
            user = package['github_user']
            name = package['github_name']
            stars = get_github_stars(user, name)
            if stars is not None:
                package['stars'] = stars
                package['url'] = 'https://github.com/{}/{}'.format(user, name)
                yield package


def get_py2_packages(packages):
    for package in packages:
        name = package['name']

        # check if overridden as Python 3
        override_status = check_overrides(name)
        if override_status is None:
            # check if cached as Python 3
            override_status = check_cache(name)

        if override_status is None:
            if not caniusepython3.check(projects=[name]):
                yield package

            else:
                write_cache(name)
        elif len(override_status) == 3:
            package['github_user'] = override_status[0]
            package['github_name'] = override_status[1]
            package['url'] = override_status[2]
            yield package

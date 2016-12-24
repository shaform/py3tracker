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
"""Generate json file for top Python 2 only packages on GitHub"""

import argparse
import json
import logging

import utils

RESULT_PATH = 'result.json'
OVERRIDE_PATH = 'overrides.json'
CACHE_PATH = 'cache.data'


def print_progress(done, total, msg=''):
    """Print progress

    :param done: how many tasks have been done
    :param msg: show text message along with the progress
    """
    percent = done / total * 100
    print('\r', end='')
    k = int(percent // 5)
    print('[{:<20s}] {}/{} ({:.1f}%) {:<10.10s}'.format('=' * k, done, total,
                                                        percent, msg),
          flush=True,
          end='')


def generate(num_package, cache, overrides):
    """Generate top package list that are Python 2 only

    :param num_package: maximum number of packages to list
    """

    top_packages = utils.get_top_packages()
    py2_packages_with_info = utils.get_py2_packages(top_packages, cache,
                                                    overrides)
    github_packages = utils.get_github_packages(py2_packages_with_info)

    top_py2_packages = []
    print_progress(0, num_package)
    for i, package in enumerate(github_packages):
        if i < num_package:
            top_py2_packages.append(package)

            # print progress
            print_progress(i + 1, num_package, package['name'])

        else:
            break
    print()

    # sort by GitHub star instead of PyPI counts
    top_py2_packages.sort(key=lambda p: (-p['stars'], -p['downloads']))
    for package in top_py2_packages:
        print(package['stars'], package['name'], package['url'])

    return top_py2_packages


def main():
    """Generate Python 2 only package list."""

    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--num-package', type=int, default=100)
    parser.add_argument('-o', '--outfile', default=RESULT_PATH)
    parser.add_argument('-c', '--cache-dir', default=CACHE_PATH)
    parser.add_argument('--overrides', default=OVERRIDE_PATH)
    parser.add_argument('-v',
                        '--verbose',
                        help='increase output verbosity',
                        action='store_true')
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)

    cache = utils.get_cache(args.cache_dir)
    overrides = utils.get_overrides(args.overrides)
    top_py2_packages = generate(args.num_package,
                                cache=cache,
                                overrides=overrides)

    with open(args.outfile, 'w', encoding='utf8') as out:
        json.dump(top_py2_packages, out)


if __name__ == '__main__':
    main()

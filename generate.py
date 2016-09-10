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

import argparse
import json
import sys

import utils


def print_progress(done, total, msg=''):
    percent = done / total * 100
    print('\r', end='')
    k = int(percent // 5)
    print('[{:<20s}] {}/{} ({:.1f}%) {:<10.10s}'.format('=' * k, done, total,
                                                        percent, msg),
          flush=True,
          end='')


def generate(outfile, num_package):
    top_packages = utils.get_top_packages()
    py2_packages = utils.get_py2_packages(top_packages)
    github_packages = utils.get_github_packages(py2_packages)

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

    top_py2_packages.sort(key=lambda p: (-p['stars'], -p['downloads']))
    for package in top_py2_packages:
        print(package['stars'], package['name'], package['url'])

    with open(outfile, 'w', encoding='utf8') as f:
        json.dump(top_py2_packages, f)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--num-package', type=int, default=100)
    parser.add_argument('-o', '--outfile', default='result.json')
    args = parser.parse_args()

    generate(args.outfile, args.num_package)

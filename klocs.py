#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Copyright © 2021 Chris Carl

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

Author:         Carl, Chris
Email:          chrisbcarl@outlook.com
Date:           2021-06-01
Description:

Thousand lines of code finder, not that KLOC is a good metric but you know.

ex)
    {prog} {version} . --not-dir node_modules .git ignoreme  --extension .py
    {prog} {version} . --gitignore .gitignore --extension .py .ps1 .c .cpp -vvv

# TODO: refactor into a library somewhere most likely
# TODO: FILE EXCLUDE like "CHANGELOG.md" so i can keep ".md"
# TODO: extensions null extension? maybe it works out of the box?
# TODO: specify what you want printed rather than using -vvvv, something like git's change filter
'''

# stdlib imports
from __future__ import absolute_import, print_function, division, with_statement  # , unicode_literals
import os
import sys
import json
import math
import fnmatch
import logging
from typing import Any, Tuple, Dict
from collections import OrderedDict

# 3rd party imports
# from builtins import *  # noqa: F401,F403  # pylint: disable=unused-wildcard-import

__version__ = '0.0.0'
FILE_RELPATH = 'klocs'
if not hasattr(sys, '_MEIPASS'):
    FILE_PATH = os.path.abspath(__file__)
else:
    FILE_PATH = os.path.abspath(os.path.join(sys._MEIPASS, FILE_RELPATH))  # pylint: disable=no-member
FILE_DIR = os.path.dirname(FILE_PATH)
FILE_NAME = os.path.splitext(os.path.basename(__file__))[0]
THIS_MODULE = sys.modules[__name__]
LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.NullHandler())
__doc__ = __doc__.format(prog=FILE_NAME, version=__version__)


def ping(*args, **kwargs):
    # type: (Tuple[Any], Dict[str, Any]) -> Tuple[str, str]
    '''Test function for all modules.

    Returns:
        'pong', __name__
    '''
    return 'pong', __name__


SANE_NOT_DIRPATH = ['.git', '.svn', 'node_modules', 'venv', '__pycache__', '.pytest_cache', '.vscode']


def abspath(*path_tokens):
    return os.path.abspath(os.path.expanduser(os.path.join(*path_tokens)))  # pylint: disable=no-value-for-parameter


def main():
    import argparse
    parser = argparse.ArgumentParser(
        prog=FILE_NAME,
        description=__doc__.format(prog=FILE_NAME),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('dirpath', type=str, help='The directory you want to analyze.')
    parser.add_argument(
        '--not-dirpath',
        type=str,
        nargs='+',
        help='Directories you dont want to iterate through. These will get added to the defaults {}'
        .format(SANE_NOT_DIRPATH)
    )
    parser.add_argument(
        '--override-not-dirpath',
        action='store_true',
        help='Instead of adding --not-dirpath to the defaults, it will replace them.'
    )
    parser.add_argument(
        '--extension',
        type=str,
        nargs='+',
        help='Extensions you want to include, by default all extensions are included.'
    )
    parser.add_argument(
        '--not-extension', type=str, nargs='+', help='Extensions you dont want to iterate through, ex) ".py" ".pyc"'
    )
    parser.add_argument(
        '--gitignore',
        type=str,
        help='if all of your ignoring strategy is encapulsated in a .gitignore, lets just use that.'
    )
    parser.add_argument(
        '-v',
        '--verbose',
        action='count',
        default=0,
        help='will print plans and tertiary analysis (-v), progress (-vv), current location (-vvv), and debug (-vvvv).'
    )
    parser.add_argument('-V', '--version', action='store_true', default=0, help='print the current version')

    if len(sys.argv) <= 1:
        parser.print_help()
        return 1
    elif len(sys.argv) == 2:
        if sys.argv[1] == '-V' or sys.argv[1] == '--version':
            print('{} {}'.format(FILE_NAME, __version__))
        return 1

    args = parser.parse_args()

    file_include_globs = []
    file_exclude_globs = []
    dir_exclude_globs = []
    gitignore_globs = []

    args.dirpath = abspath(args.dirpath)
    if not os.path.isdir(args.dirpath):
        raise OSError('provided dirpath "{}" does not exist'.format(args.dirpath))
    if args.gitignore is not None:
        args.gitignore = abspath(args.gitignore)
        with open(args.gitignore) as r:
            for line in r.read().splitlines():
                tokens = line.split('#')
                if len(tokens) >= 1:
                    token = tokens[0].strip()
                    if len(token) > 0:
                        gitignore_globs.append(token)
    args.not_dirpath = args.not_dirpath or []
    if not args.override_not_dirpath:
        args.not_dirpath += SANE_NOT_DIRPATH
    for i, not_dirpath in enumerate(args.not_dirpath):
        not_dirpath_posix = not_dirpath.replace('\\', '/')
        if '../' in not_dirpath_posix:
            not_dirpath_posix = not_dirpath_posix.replace('../', '')
        if not_dirpath_posix.endswith('/'):
            not_dirpath_posix = not_dirpath_posix[0:-1]
        # if there's a file with the same name it would be excluded so we stay dir specific.
        dir_exclude_globs.append('*/{}'.format(not_dirpath_posix))
    args.extension = args.extension or []
    for i, extension in enumerate(args.extension):
        if not extension.startswith('.'):
            args.extension[i] = '.' + extension
        file_include_globs.append('**{}'.format(args.extension[i]))
    args.not_extension = args.not_extension or []
    for i, not_extension in enumerate(args.not_extension):
        if not not_extension.startswith('.'):
            args.not_extension[i] = '.' + not_extension
        file_exclude_globs.append('**{}'.format(args.not_extension[i]))

    if args.verbose >= 1:
        print('scanning "{}"...'.format(args.dirpath))
        if file_include_globs:
            print('including files:')
            print('\n'.join('  - {}'.format(e) for e in file_include_globs))
        if file_exclude_globs:
            print('excluding files:')
            print('\n'.join('  - {}'.format(e) for e in file_exclude_globs))
        if dir_exclude_globs:
            print('excluding dirs:')
            print('\n'.join('  - {}'.format(e) for e in dir_exclude_globs))
        if gitignore_globs:
            print('.gitignore:')
            print('\n'.join('  - {}'.format(e) for e in gitignore_globs))

    cwd = os.getcwd()
    try:
        pass
        os.chdir(args.dirpath)
        ignored_dirs = OrderedDict()
        included_dirs = OrderedDict()
        extension_frequency = OrderedDict()
        filepaths = []
        locs = 0
        power_frequency = OrderedDict()
        max_power = 0
        base = 2

        # analyzing the dirs for filtration
        # this way can display progress
        if args.verbose >= 2:
            print('analyzing directories in "{}"...'.format(args.dirpath))
        dirs_to_analyze = [abspath(e) for e in os.listdir(args.dirpath) if os.path.isdir(abspath(e))]
        for dirpath, _, basenames in os.walk(args.dirpath):
            try:
                dir_analysis_idx = dirs_to_analyze.index(dirpath)
                if dir_analysis_idx > -1:
                    if args.verbose >= 2:
                        print(
                            '  - dir analysis {} / {} - {:0.2f}%'.format(
                                dir_analysis_idx, len(dirs_to_analyze), (dir_analysis_idx) / len(dirs_to_analyze) * 100
                            )
                        )
            except ValueError:
                pass

            if any(dirpath.startswith(e) for e in ignored_dirs):
                if args.verbose >= 4:
                    print('    - skipping "{}"'.format(dirpath))
                continue

            if (
                (len(dir_exclude_globs) > 0 and any(fnmatch.fnmatch(dirpath, e) for e in dir_exclude_globs))
                or (len(gitignore_globs) > 0 and any(fnmatch.fnmatch(dirpath, e) for e in gitignore_globs))
            ):
                ignored_dirs[dirpath] = True
                if args.verbose >= 3:
                    print('    - skipping "{}"'.format(dirpath))
                continue
            else:
                included_dirs[dirpath] = True
                if args.verbose >= 3:
                    print('    - including "{}"'.format(dirpath))
                for basename in basenames:
                    filepath = os.path.join(dirpath, basename)
                    filepaths.append(filepath)
        if args.verbose >= 2:
            print('  - dir analysis {} / {} - 100.00%'.format(dir_analysis_idx + 1, len(dirs_to_analyze)))

        # analyzing the files for filtration
        # this way can display progress bar
        if args.verbose >= 2:
            print('analyzing {} files in "{}"...'.format(len(filepaths), args.dirpath))
        tenths = 0
        ten_percent = len(filepaths) // 10
        next_maker = ten_percent * tenths
        filtered_filepaths = []
        for i, filepath in enumerate(filepaths):
            if i >= next_maker:
                tenths += 1
                if args.verbose >= 2:
                    print('  - file analysis {} / {} - {:0.2f}%'.format(i, len(filepaths), (i) / len(filepaths) * 100))
                next_maker = ten_percent * tenths

            if args.verbose >= 4:
                print('  - viewing "{}"'.format(filepath))
            if len(file_include_globs) == 0 or any(fnmatch.fnmatch(filepath, e) for e in file_include_globs):
                if args.verbose >= 4:
                    print('  - checking "{}"'.format(filepath))
                if not (
                    (len(file_exclude_globs) > 0 and any(fnmatch.fnmatch(filepath, e) for e in file_exclude_globs)) or
                    (len(gitignore_globs) > 0 and any(fnmatch.fnmatch(filepath, e) for e in gitignore_globs))
                ):
                    if args.verbose >= 3:
                        print('  - found "{}"'.format(filepath))
                    with open(filepath) as r:
                        file_locs = len(r.readlines())
                    locs += file_locs
                    try:
                        loc_power = int(math.log(file_locs, base))
                    except ValueError:
                        # got 0 lines
                        loc_power = 0
                    if loc_power > max_power:
                        max_power = loc_power
                    if loc_power not in power_frequency:
                        power_frequency[loc_power] = []
                    relpath = os.path.relpath(filepath, args.dirpath).replace('\\', '/')
                    power_frequency[loc_power].append((relpath, file_locs))
                    _, ext = os.path.splitext(filepath)
                    if ext not in extension_frequency:
                        extension_frequency[ext] = 0
                    extension_frequency[ext] += 1
                    filtered_filepaths.append(filepath)
        if args.verbose >= 2:
            print('  - file analysis {} / {} - 100.00%'.format(i + 1, len(filepaths)))

        if len(filtered_filepaths) == 0:
            raise ValueError('found 0 files')
        else:
            if args.verbose >= 1:
                print('tertiary analysis:')
                print(
                    '  - dir count: {}; ignored: {}; filtered: {}'.format(
                        len(ignored_dirs) + len(included_dirs), len(ignored_dirs), len(included_dirs)
                    )
                )
                print(
                    '  - file count: {}; ignored: {}; filtered: {}'.format(
                        len(filepaths),
                        len(filepaths) - len(filtered_filepaths), len(filtered_filepaths)
                    )
                )
                print('  - extension frequency: {}'.format(json.dumps(extension_frequency)))
                print('  - loc power frequency')
                for power in range(0, max_power + 1):
                    if power in power_frequency:
                        print(
                            '    - [{:06}] {}^{}: {} / {} - {:0.2f}%'.format(
                                base**power, base, power, len(power_frequency[power]), len(filtered_filepaths),
                                (len(power_frequency[power]) / len(filtered_filepaths)) * 100
                            )
                        )

                        if args.verbose >= 3:
                            condition = True
                        else:
                            condition = power >= max_power - 2

                        if condition:
                            for i, tpl in enumerate(power_frequency[power]):
                                relpath, file_locs = tpl
                                print('      - {} - {}'.format(relpath, file_locs))
                                if args.verbose < 4:
                                    if i > 9:
                                        if i < len(power_frequency[power]) - 1:
                                            print(
                                                '      - {} more files...'.format(len(power_frequency[power]) - i - 1)
                                            )
                                        break
                print(
                    'locs: {}; avg locs / file: {}; file count: {}'.format(
                        locs, locs / len(filtered_filepaths), len(filtered_filepaths)
                    )
                )
        print('{:0.2f} KLOCs'.format(locs / 1000))

    except Exception:
        LOGGER.error('something happened in directory', exc_info=True)
        return 1
    os.chdir(cwd)
    return 0


if __name__ == '__main__':
    sys.exit(main())

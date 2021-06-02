# klocs
Measures klocs, pretty standard stuff.

# Installation
```bash
/usr/bin/python2 -m pip install -r requirements.txt
# typing already part of python3
```

# Usage
## Typical
```bash
python klocks.py .  # will only print the number of klocs
python klocks.py ../some-other-folder  # will only print the number of klocs
python klocks.py ../some-other-folder -v  # some verbosity and statistics at the end.
```

## Arguments
```
usage: klocs [-h] [--not-dirpath NOT_DIRPATH [NOT_DIRPATH ...]] [--override-not-dirpath] [--extension EXTENSION [EXTENSION ...]] [--not-extension NOT_EXTENSION [NOT_EXTENSION ...]] [--gitignore GITIGNORE] [-v] dirpath

positional arguments:
  dirpath               The directory you want to analyze.

optional arguments:
  -h, --help            show this help message and exit
  --not-dirpath NOT_DIRPATH [NOT_DIRPATH ...]
                        Directories you dont want to iterate through. These will get added to the defaults ['.git', '.svn', 'node_modules', 'venv', '__pycache__', '.pytest_cache', '.vscode']
  --override-not-dirpath
                        Instead of adding --not-dirpath to the defaults, it will replace them.
  --extension EXTENSION [EXTENSION ...]
                        Extensions you want to include, by default all extensions are included.
  --not-extension NOT_EXTENSION [NOT_EXTENSION ...]
                        Extensions you dont want to iterate through, ex) ".py" ".pyc"
  --gitignore GITIGNORE
                        if all of your ignoring strategy is encapulsated in a .gitignore, lets just use that.
  -v, --verbose         will print plans and tertiary analysis (-v), progress (-vv), current location (-vvv), and debug (-vvvv).
```
- not-dirpath - is a space-separated list of directory paths that if encountered will be skipped.
- extension - if provided, it will limit all findings to the exact extensions provided. using --extension and --not-extension doesn't make sense and only --extension will be honored.
- not-extension - the opposite of extension, if provided, then out of all extensions that could be found, if an extension matches something from not-extension, then it will not be included.
- gitignore - if you have a `.gitignore` handy, it may be worth providing the `.gitignore` path and this will serve to limit any files and directores that match the `.gitignore` contents. comments are ignored

### Verbosity
- v - will print the arguments given including what it's ignoring, what extensions its looking for, and the tertiary analysis which contains things like filecount, extension frequency, a bucket list of word counts, etc.
- vv - will print progress percentages as it traverses a tree
- vvv - will print what it finds as it finds it and will print the first 10 files it encountered that match a particular bucket in the tertiary analysis
- vvvv - will print every dir that it ignored and every file that didn't pass the extension and gitignore filtration as well as ALL files that fit a particular bucket in the tertiary analysis

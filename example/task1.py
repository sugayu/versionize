'''Task 1
'''

import os
from pathlib import Path
from versionize import Version

if Path.cwd().name == 'versionize':
    os.chdir('example')

__version__ = '1.0.1'
dir_save = 'task1/'
version = Version(__version__, dir_save)


##
@version.decorator('filesave.txt')
def main(a, savepath: Path):
    with savepath.open('w') as f:
        f.write(f'This is Task 1: input = {a}')


if __name__ == '__main__':
    a = 3
    main(a)

'''Task 2
'''

import os
from pathlib import Path
from versionize import Version

if Path.cwd().name == 'versionize':
    os.chdir('example')

__version__ = '1.0.2'
dir_save = 'task2/'
version = Version(__version__, dir_save)


##
@version.decorator('parameter.txt')
def main(a, savepath: Path):
    with savepath.open('w') as f:
        f.write(f'This is Task 2: input = {a}')


if __name__ == '__main__':
    a = 4
    main(a)

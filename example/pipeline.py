'''Pipeline
'''

import os
from pathlib import Path
from logging import getLogger
from sugayutils.log import mylogconfig

if Path.cwd().name == 'versionize':
    os.chdir('example')

import task1
import task2

mylogconfig()
logger = getLogger(__name__)

__version__ = '1.0.0'


##
def main() -> None:
    '''Main function of the pipeline.'''
    a = 4
    task1.main(a, version_flow=__version__)

    b = 2
    task2.main(b, version_flow=task1.__version__)


if __name__ == '__main__':
    main()

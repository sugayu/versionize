'''Pipeline
'''

import os
from pathlib import Path
from logging import getLogger
from sugayutils.log import mylogconfig
from versionize import VersionFlow

if Path.cwd().name == 'versionize':
    os.chdir('example')

import task1
import task2

mylogconfig()
logger = getLogger(__name__)

__major_version__ = '1.0.0'


##
def main() -> None:
    '''Main function of the pipeline.'''
    vflow = VersionFlow(__major_version__)

    a = 4
    task1.main(a, version_flow=vflow)

    b = 2
    task2.main(b, version_flow=vflow)


if __name__ == '__main__':
    main()

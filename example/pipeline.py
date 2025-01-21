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

__version__ = '1.0.0'


##
def main() -> None:
    '''Main function of the pipeline.'''
    vflow = VersionFlow(__version__)

    a = 4
    task1.main(a, version_flow=vflow.current_version)

    b = 2
    task2.main(b, version_flow=vflow(task1.__version__))


if __name__ == '__main__':
    main()

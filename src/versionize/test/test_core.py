from pathlib import Path
from ..core import Version, VersionFlow
from logging import getLogger

logger = getLogger(__name__)


# main version
__major_version__ = '0.0.1'


##
def test_dryrun() -> None:
    vflow = VersionFlow(__major_version__)
    vflow.is_dryrun = True

    a = 4
    task(a, version_flow=vflow)


# subversion
__version__ = '0.0.2'
dir_save = 'task1/'
version = Version(__version__, dir_save)


@version.decorator('filesave.txt')
def task(a, savepath: Path):
    logger.info('Doing task')

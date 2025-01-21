'''Core contents of versionize package.
'''

from typing import Callable
from functools import wraps
from pathlib import Path
from packaging.version import Version as _Version
import json
from logging import getLogger

__all__ = ['Version']
logger = getLogger('versionize')


##
class Version:
    '''Versionize main class.

    This class controles three types of versions:
    - version_code:
    - version_flow:
    - version_record:
    '''

    metafilename = '.metaversion'
    version_initial = '0.0.0'
    _dirname_root = 'results'
    _prefix = 'v'

    def __init__(
        self,
        version_code: str,
        dirname: str | Path,
        dirname_root: str = _dirname_root,
    ) -> None:
        self.version_code = version_code
        self.dirname_root = Path(dirname_root)
        self._dirname = dirname
        self._meta: dict = {}
        self._meta_root: dict = {}
        self.path: Path

        self.dirname_root.mkdir(exist_ok=True)

    def decorator(self, tag: str, skip: bool = True) -> Callable:
        '''Decorator for taks functions.'''

        def _decorator(func) -> Callable:

            @wraps(func)
            def versionized_wrapper(
                *args, version_flow: str = self.version_code, **kwargs
            ):
                version_record = self.get_version_of(tag)
                new_version = max(_Version(version_flow), _Version(self.version_code))
                logger.debug(f'version_record={version_record}')
                logger.debug(f'version_code={self.version_code}')
                logger.debug(f'version_flow={version_flow}')

                if _Version(version_record) >= new_version:
                    if skip:
                        msg = (
                            f'{func.__module__}.{func.__name__}(): '
                            f'The version {version_record} is the latest. Skip the task.'
                        )
                        logger.info(msg)
                        return

                dsave = self.to_directory(new_version)
                dsave.mkdir(exist_ok=True, parents=True)
                savepath = dsave / tag

                # Main function
                value = func(*args, savepath=savepath, **kwargs)

                self.up(tag, new_version)
                return value

            return versionized_wrapper

        return _decorator

    def up(self, tag: str, new_version: str | _Version) -> None:
        '''Update version records.'''
        if isinstance(new_version, _Version):
            new_version = str(new_version)

        self.meta_root[self.dirname_root.name] = new_version
        self._write(self.dirname_root, self.meta_root)

        directory = self.to_directory(new_version)
        meta = self._read(directory)
        meta[tag] = new_version
        self._write(directory, meta)
        logger.info(f'Version updated: {tag} = {new_version}')

    @property
    def version_root(self) -> str:
        return self.meta_root.get(self.dirname_root.name, self.version_initial)

    @property
    def directory(self) -> Path:
        return self.to_directory(self.version_root)

    @property
    def meta_root(self) -> dict:
        # FIXME: Change meta_root if it's not current meta root.
        if not self._meta_root:
            self._meta_root = self._read(self.dirname_root)
        return self._meta_root

    @property
    def meta(self) -> dict:
        if not self._meta:
            self._meta = self._read(self.directory)
        return self._meta

    def get_version_of(self, tag: str) -> str:
        '''Get a version recoreded in a meta file.'''
        return self.meta.get(tag, self.version_initial)

    def to_directory(self, version: str | _Version) -> Path:
        vdir = self.to_dirname(version)
        return self.dirname_root / vdir / self._dirname

    def to_dirname(self, version: str | _Version) -> str:
        '''Make dirname from the input version.'''
        if isinstance(version, str):
            version = _Version(version)
        return self._prefix + str(version.major)

    def _read(self, pwd: Path) -> dict:
        '''Read metafile that records versions.'''
        if not pwd.exists():
            pwd.mkdir(exist_ok=True, parents=True)
            self._write(pwd, {})
            return {}

        p = pwd / self.metafilename
        if p.exists():
            with p.open() as f:
                return json.load(f)
        else:
            return {}

    def _write(self, pwd: Path, meta: dict) -> None:
        '''Write metafile that records versions.'''
        p = pwd / self.metafilename
        with p.open('w') as f:
            json.dump(meta, f)

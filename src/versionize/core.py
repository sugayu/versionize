'''Core contents of versionize package.
'''

from typing import Callable
from functools import wraps
from pathlib import Path
from packaging.version import Version as _Version
import json
from logging import getLogger

__all__ = ['Version', 'VersionFlow']
logger = getLogger('versionize')


##
class Version:
    '''Versionize main class.

    This class is presumed to be used in tasks.
    This class controles three types of versions:
    - version_code: a version of a script code
    - version_record: a version of a file/files recorded in .metaversion
    - version_flow: a version of the pipeline flow
    '''

    metafilename = '.metaversion'
    version_initial = '0.0.0'
    _dirname_root = 'results'
    _prefix = 'v'

    def __init__(
        self,
        version_code: str | _Version,
        dirname: str | Path,
        dirname_root: str = _dirname_root,
    ) -> None:
        if isinstance(version_code, _Version):
            self.version_code = version_code
        else:
            self.version_code = _Version(version_code)
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
                *args, version_flow: str | _Version = self.version_code, **kwargs
            ):
                version_record = self.get_version_of(tag)
                if isinstance(version_flow, str):
                    version_flow = _Version(version_flow)
                new_version: _Version = max(version_flow, self.version_code)
                logger.debug(f'version_record={str(version_record)}')
                logger.debug(f'version_code={str(self.version_code)}')
                logger.debug(f'version_flow={str(version_flow)}')

                if version_record >= new_version:
                    if skip:
                        msg = (
                            f'The version {version_record} of {tag} is the latest. '
                            f'Skip {func.__module__}.{func.__name__}().'
                        )
                        logger.info(msg)
                        return

                dsave = self.to_directory(new_version)
                dsave.mkdir(exist_ok=True, parents=True)
                savepath = dsave / tag

                # Main function
                value = func(*args, savepath=savepath, **kwargs)

                self.update(tag, new_version)
                return value

            return versionized_wrapper

        return _decorator

    def update(self, tag: str, new_version: str | _Version) -> None:
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

    def get_version_of(self, tag: str) -> _Version:
        '''Get a version recoreded in a meta file.'''
        return _Version(self.meta.get(tag, self.version_initial))

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


class VersionFlow:
    '''Return the highest version in the pipeline flow.

    This class is presumed to be used in pipelines.

    NOTE:
        This class is thought to be used like a function,
        but it makes use of a side effect.
    '''

    def __init__(self, version_initial: str) -> None:
        self.current_version = _Version(version_initial)

    def __call__(self, version_flow: str | _Version) -> str:
        if isinstance(version_flow, str):
            version_flow = _Version(version_flow)
        new_version = max(self.current_version, version_flow)
        self.current_version = new_version
        return str(new_version)

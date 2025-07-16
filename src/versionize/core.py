'''Core contents of versionize package.
'''

from typing import Callable, Self
from functools import wraps
from pathlib import Path
from packaging.version import Version as _Version
import copy
import json
from logging import getLogger

__all__ = ['Version', 'VersionFlow']
logger = getLogger('versionize')


##
class Version:
    '''Versionize main class.

    This class is presumed to be used in tasks.
    This class controls three types of versions:
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

    def decorator(
        self,
        tag: str,
        always_run: bool = False,
        returns: str | tuple[str, ...] | bool = False,
    ) -> Callable:
        '''Decorator for taks functions.'''

        def _decorator(func) -> Callable:

            @wraps(func)
            def versionized_wrapper(
                *args,
                version_flow: VersionFlow | None = None,
                **kwargs,
            ):
                version_record = self.get_version_of(tag)

                if version_flow is None:
                    version_flow = VersionFlow(str(self.version_code))
                version_current = version_flow.current_version

                logger.debug(f'version_record={str(version_record)}')
                logger.debug(f'version_code={str(self.version_code)}')
                logger.debug(f'version_flow={str(version_current)}')

                # New versions
                new_version: _Version = max(version_current, self.version_code)
                dsave = self.to_directory(new_version)
                savepath = dsave / tag

                # Return values
                return_values: None | tuple[Path, ...] | Path
                if returns is True:
                    return_values = savepath
                elif isinstance(returns, tuple):
                    return_values = tuple(Path(str(savepath) + r) for r in returns)
                elif isinstance(returns, str):
                    return_values = Path(str(savepath) + returns)
                else:
                    return_values = None

                is_new = new_version > version_record
                do_parallel = version_flow.do_parallel(new_version)
                if always_run or is_new or do_parallel:
                    dsave.mkdir(exist_ok=True, parents=True)

                    if version_flow.is_dryrun:  # dryrun
                        self.dryrun(tag, new_version)
                        value = return_values

                    else:  # Main routine
                        value = func(*args, savepath=savepath, **kwargs)
                        if is_new:
                            self.update(tag, new_version)
                        elif always_run:
                            self.stay(tag, new_version, always_run=True)
                        elif do_parallel:
                            self.stay(tag, new_version, do_parallel=True)

                    if version_flow.in_parallel:
                        version_flow.set_parallel(new_version)

                else:
                    msg = (
                        f'The version {version_record} of {tag} is the latest. '
                        f'Skip {func.__module__}.{func.__name__}().'
                    )
                    logger.info(msg)
                    value = return_values

                version_flow(new_version)
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
        logger.info(
            'Version updated: '
            f'{self.dirname_root.name} {self.directory.name} {tag} = {new_version}'
        )

    def stay(
        self,
        tag,
        new_version: str | _Version,
        always_run: bool = False,
        do_parallel: bool = False,
    ) -> None:
        '''Stay version records.'''
        if isinstance(new_version, _Version):
            new_version = str(new_version)

        info = f'{self.dirname_root.name} {self.directory.name} {tag} = {new_version}'
        if always_run:
            logger.info(f'Always run: {info}')
        if do_parallel:
            logger.info(f'Parallel run: {info}')

    def dryrun(self, tag: str, new_version: str | _Version) -> None:
        '''Dryrun of a pipeline and tasks.'''
        if isinstance(new_version, _Version):
            new_version = str(new_version)
        logger.info(
            '(Dryrun) Version updated: '
            f'{self.dirname_root.name} {self.directory.name} {tag} = {new_version}'
        )

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
        self.is_dryrun = False
        self.in_parallel = False
        self.version_start_parallel = _Version('9999.0.0')
        self.version_parallel = _Version('9999.0.0')

    def __call__(self, version_flow: str | _Version) -> Self:
        if isinstance(version_flow, str):
            version_flow = _Version(version_flow)
        new_version = max(self.current_version, version_flow)
        self.current_version = new_version
        return self

    def branch(self, parallel: bool = False) -> Self:
        '''Copy myself to make a branch of the flow.'''
        new = copy.deepcopy(self)
        new.in_parallel = parallel
        if parallel:
            new.version_start_parallel = self.current_version
        return new

    @property
    def versionlog(self) -> str:
        return f'Running pipeline version: v{self.current_version}'

    def do_parallel(self, new_version) -> bool:
        return new_version >= self.version_parallel

    def set_parallel(self, new_version) -> None:
        if new_version < self.version_parallel:
            self.version_parallel = new_version

    def parallelback(self) -> None:
        if self.version_start_parallel == _Version('9999.0.0'):
            raise ValueError('Not in parallel run.')
        self.current_version = self.version_start_parallel

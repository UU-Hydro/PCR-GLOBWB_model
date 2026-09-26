import datetime
import functools
import json
import logging
import logging.handlers
import os
import pathlib
import platform
import signal
import subprocess
import sys
import time
from importlib.metadata import PackageNotFoundError, version

from rich.console import Console
from rich.logging import RichHandler
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

_FORMAT = "%(asctime)s [%(sim_date)s] %(levelname)-8s %(name)s: %(message)s"
_NO_SIMULATION_DATE = "----------"

logger = logging.getLogger(__name__)

_console_handler = None
_file_handler = None
_run_start = None
_log_file = None
_manifest = {}
_simulation_date = _NO_SIMULATION_DATE
_progress_bar = None


class _SimulationDateFilter(logging.Filter):
    def filter(self, record):
        record.sim_date = _simulation_date
        return True


_FORMATTER = logging.Formatter(_FORMAT, datefmt="%Y-%m-%dT%H:%M:%S%z")
_DATE_FILTER = _SimulationDateFilter()


def add_log_level_arguments(parser):
    """Add --log-level (console) and --file-level (run.log), both default INFO."""
    for flag, target in [("--log-level", "console"), ("--file-level", "run.log")]:
        parser.add_argument(
            flag,
            type=str.upper,
            choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            default="INFO",
            help="%s log level (default INFO)" % target,
        )


def start_logging(console_level="INFO", file_level="INFO"):
    """Log to stderr now and hold the run.log records until ``set_log_dir``."""
    global _console_handler, _file_handler, _run_start, _log_file, _manifest
    global _simulation_date
    # rich only on a terminal: redirected (e.g. SLURM) output would be wrapped at 80 columns
    if sys.stderr.isatty():
        console_handler = RichHandler(
            console=Console(stderr=True),
            show_path=False,
            rich_tracebacks=True,
            log_time_format="%b %d %H:%M:%S",
            omit_repeated_times=False,
        )
        # RichHandler prints the time and level itself
        console_handler.setFormatter(
            logging.Formatter("[%(sim_date)s] %(name)s: %(message)s")
        )
    else:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setFormatter(_FORMATTER)
    console_handler.setLevel(console_level)
    file_handler = logging.handlers.MemoryHandler(capacity=100_000)
    file_handler.setLevel(file_level)
    file_handler.setFormatter(_FORMATTER)

    root = logging.getLogger()
    for handler in (_console_handler, _file_handler):
        if handler is not None:
            root.removeHandler(handler)
            handler.close()

    _console_handler, _file_handler = console_handler, file_handler
    for handler in (_console_handler, _file_handler):
        handler.addFilter(_DATE_FILTER)
        root.addHandler(handler)
    root.setLevel(min(_console_handler.level, _file_handler.level))

    _run_start = time.monotonic()
    _manifest = _collect_run_info()
    _log_file = None
    _simulation_date = _NO_SIMULATION_DATE


def set_log_dir(log_dir):
    """Write the held records and all later ones to ``<log_dir>/run.log``; returns its path."""
    global _file_handler, _log_file
    if not isinstance(_file_handler, logging.handlers.MemoryHandler):
        raise RuntimeError("set_log_dir must follow start_logging, once")
    log_dir = pathlib.Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    _log_file = log_dir / "run.log"

    file_handler = logging.FileHandler(_log_file, encoding="utf-8")
    file_handler.setLevel(_file_handler.level)
    file_handler.setFormatter(_FORMATTER)
    file_handler.addFilter(_DATE_FILTER)

    root = logging.getLogger()
    root.removeHandler(_file_handler)
    _file_handler.setTarget(file_handler)
    _file_handler.close()
    root.addHandler(file_handler)
    _file_handler = file_handler

    logger.info("Logging output to %s", _log_file)
    # written now as well as at the end, so a run killed with SIGKILL still has one
    _write_manifest(status="running")
    return _log_file


def _command_output(args):
    """Stripped stdout of ``args``, or None if the command is missing or fails."""
    try:
        result = subprocess.run(args, capture_output=True, text=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip()


def _collect_run_info():
    """What was run, where and with which versions, taken when logging starts."""
    source_dir = str(pathlib.Path(__file__).resolve().parent)
    git_status = _command_output(
        ["git", "-C", source_dir, "status", "--porcelain", "--untracked-files=no"]
    )
    # modules are looked up, not imported: only libraries the run loaded are listed
    libraries = {
        name: getattr(sys.modules.get(name), "__version__", None)
        for name in ("numpy", "netCDF4", "pcraster")
    }
    libraries["gdal"] = _command_output(["gdalinfo", "--version"])
    try:
        package_version = version("pcrglobwb")
    except PackageNotFoundError:
        package_version = None
    return {
        "started": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "command": sys.argv,
        "working_directory": os.getcwd(),
        "host": platform.node(),
        "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
        "os": "%s %s" % (platform.system(), platform.release()),
        "python": platform.python_version(),
        "environment": {
            name: os.environ.get(name)
            for name in ("PATH", "PYTHONPATH", "PCRASTER_NR_WORKER_THREADS")
        },
        "pcrglobwb_version": package_version,
        "git_commit": _command_output(["git", "-C", source_dir, "rev-parse", "HEAD"]),
        "git_uncommitted_changes": None if git_status is None else git_status != "",
        "libraries": libraries,
    }


def set_simulation_date(date):
    """Stamp every following log line with ``date`` (a date or datetime)."""
    global _simulation_date
    _simulation_date = date.strftime("%Y-%m-%d")


class TimeStepProgress:
    """Sets the simulation date and logs progress for one PCRaster time loop.

    Create it just before the loop starts, call ``start_step`` at the start of
    every time step and ``end_step`` at its end. A progress line is logged when a
    step closes a simulation year or the loop, so each spin-up year, which runs
    as a loop of its own, always gets one. The finish estimate covers this loop
    only.
    """

    def __init__(self, total_steps):
        self._total_steps = total_steps
        self._start = time.monotonic()
        self._step = None
        self._date = None
        self._bar = None

    def start_step(self, step, date):
        global _progress_bar
        self._step = step
        self._date = date
        set_simulation_date(date)
        # the bar shares the RichHandler's console so log lines print above it
        if self._bar is None and isinstance(_console_handler, RichHandler):
            self._bar = Progress(
                TextColumn("{task.description}"),
                BarColumn(),
                MofNCompleteColumn(),
                TimeElapsedColumn(),
                TextColumn("eta"),
                TimeRemainingColumn(),
                console=_console_handler.console,
                transient=True,
            )
            self._task = self._bar.add_task("", total=self._total_steps)
            self._bar.start()
            _progress_bar = self._bar
        if self._bar is not None:
            self._bar.update(
                self._task, description=date.strftime("%Y-%m-%d"), completed=step - 1
            )

    def end_step(self, end_of_year):
        if self._bar is not None:
            self._bar.update(self._task, completed=self._step)
            if self._step >= self._total_steps:
                self._bar.stop()
        if not end_of_year and self._step < self._total_steps:
            return

        elapsed = time.monotonic() - self._start
        remaining = elapsed / self._step * (self._total_steps - self._step)
        finish = datetime.datetime.now().astimezone() + datetime.timedelta(
            seconds=remaining
        )
        logger.info(
            "Progress: simulated up to %s; %d of %d time steps (%.0f%%); elapsed %s; "
            "estimated finish %s (in %s)",
            self._date.strftime("%Y-%m-%d"),
            self._step,
            self._total_steps,
            100 * self._step / self._total_steps,
            datetime.timedelta(seconds=round(elapsed)),
            finish.isoformat(timespec="seconds"),
            datetime.timedelta(seconds=round(remaining)),
        )


def _log_run_end(status):
    # a failed run leaves its bar running, and with it the terminal cursor hidden
    if _progress_bar is not None:
        _progress_bar.stop()
    level = logging.INFO if status == "success" else logging.CRITICAL
    if _log_file is None:
        logger.log(level, "Run finished: %s, before run.log was opened", status)
        return
    wall_seconds = time.monotonic() - _run_start
    wall_time = datetime.timedelta(seconds=round(wall_seconds))
    logger.log(
        level,
        "Run finished: %s; wall time %s; log file %s",
        status,
        wall_time,
        _log_file,
    )
    _write_manifest(
        status=status,
        finished=datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        wall_time_seconds=round(wall_seconds, 1),
    )


def _write_manifest(**run_state):
    manifest = dict(_manifest, **run_state, log_file=str(_log_file))
    (_log_file.parent / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


class _Terminated(BaseException):
    """Raised on SIGTERM; a BaseException so ``except Exception`` cannot swallow it."""


def _raise_terminated(signum, frame):
    raise _Terminated


def log_run_status(main):
    """Wrap an entry point so every run ends with a status line in run.log.

    Unhandled errors are logged with their traceback and exit with code 1, Ctrl-C
    exits with 130 and SIGTERM (SLURM time limit, scancel) with 143. Any sys.exit raised inside ``main`` counts as a failure, even
    sys.exit() or sys.exit(0), since the run did not complete; an integer code
    other than 0 is kept, anything else becomes 1. A sys.exit before
    ``start_logging``, such as argparse's --help or a usage error, passes through.
    """

    @functools.wraps(main)
    def wrapper(*args, **kwargs):
        previous_handler = signal.signal(signal.SIGTERM, _raise_terminated)
        try:
            result = main(*args, **kwargs)
        except KeyboardInterrupt:
            _log_run_end("interrupted")
            raise SystemExit(130)
        except _Terminated:
            _log_run_end("terminated")
            raise SystemExit(143)
        except SystemExit as exit_request:
            if _run_start is None:
                raise
            code = exit_request.code
            exit_code = code if isinstance(code, int) and code != 0 else 1
            if isinstance(code, str):
                logger.critical("Run stopped: %s", code, exc_info=True)
            else:
                logger.critical("Run stopped by sys.exit(%r)", code, exc_info=True)
            _log_run_end("failed")
            raise SystemExit(exit_code)
        except Exception:
            logger.critical("Unhandled error", exc_info=True)
            _log_run_end("failed")
            raise SystemExit(1)
        finally:
            signal.signal(signal.SIGTERM, previous_handler)
        _log_run_end("success")
        return result

    return wrapper

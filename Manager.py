import os
import subprocess
import time
from pathlib import Path
from typing import Optional

from Configuration import Configuration

THIRTY_MINUTES_IN_SECONDS: int = 30 * 60

class Pipe:
    """
    A thin utility wrapper around os.pipe and related close operations
    """

    def __init__(self):

        self._read_fd: int
        self._write_fd: int
        self._read_fd, self._write_fd = os.pipe()

        self.read_closed: bool = False
        self.write_closed: bool = False

    @property
    def read_fd(self) -> Optional[int]:

        if self.read_closed:
            return None

        return self._read_fd

    @property
    def write_fd(self) -> Optional[int]:

        if self.write_closed:
            return None

        return self._write_fd

    def write_and_flush(self, content: str) -> bool:

        if self.write_closed:
            return False

        with os.fdopen(self._write_fd, 'w', encoding='utf-8') as pipe_writer:
            # Now you can write normal strings
            pipe_writer.write(content + "\n")

            # Force the data out of the application buffer into the pipe
            pipe_writer.flush()

        return True

    def read_next_line_blocking(self) -> Optional[str]:

        if self.read_closed:
            return None

        with os.fdopen(self._read_fd, 'r') as pipe_reader:

            # this is a blocking read - it will suspend the current thread until something is available to return
            next_line: str = pipe_reader.read()

        return next_line

    def close_read(self):

        if self.read_closed:
            return

        os.close(self._read_fd)
        self.read_closed = True

    def close_write(self):

        if self.write_closed:
            return

        os.close(self._write_fd)
        self.write_closed = True

    def close_all(self):

        self.close_read()
        self.close_write()


class PictureViewerManager:

    def __init__(self):

        self.full_path_to_picture_viewer_two_directory: Optional[str] = \
            Configuration.get_config().get_viewer_directory()
        self.viewer_process: Optional[subprocess.Popen] = None
        self.manager_to_viewer_pipe: Optional[Pipe] = None
        self.viewer_to_manager_pipe: Optional[Pipe] = None
        self._is_viewer_running: bool = False

    def launch_viewer_as_process(self) -> bool:

        # in order to run in the correct virtual environment we need to specify the python executable in the target
        # environments bin directory
        python_in_picture_viewer_env: str = \
            os.path.join(self.full_path_to_picture_viewer_two_directory, ".venv", "bin", "python")

        self.manager_to_viewer_pipe = Pipe()
        self.viewer_to_manager_pipe = Pipe()

        self.viewer_process = subprocess.Popen(
            args = [
                python_in_picture_viewer_env,
                "PictureViewerApp.py",
                "--",
                "--windowed", # this is for debug only
                "--allow-mouse-input", # this is also for debug
                "--no-workers", # also for debug
                # pass the write file fd of the viewer-to-manager pipe to the viewer
                f"--to-manager-pipe={self.viewer_to_manager_pipe.write_fd}",
                # pass the read fd of the manager-to-viewer pipe to the viewer
                f"--to-viewer-pipe={self.manager_to_viewer_pipe.read_fd}"
            ],
            cwd=self.full_path_to_picture_viewer_two_directory,
            pass_fds=[self.viewer_to_manager_pipe.write_fd, self.manager_to_viewer_pipe.read_fd]
        )

        # really important to close the descriptors not used by this manager - otherwise this process will hang waiting
        # for itself to read or write
        self.viewer_to_manager_pipe.close_write()
        self.manager_to_viewer_pipe.close_read()

        self._is_viewer_running = True

        return True

    def stop_viewer(self):

        if self.viewer_process:

            self.manager_to_viewer_pipe.write_and_flush("request-stop")

            status: Optional[int] = self.viewer_process.poll()
            while status is None:
                time.sleep(5)
                status = self.viewer_process.poll()

            self._is_viewer_running = False

    def close_pipes(self):

        if self.manager_to_viewer_pipe:
            self.manager_to_viewer_pipe.close_all()

        self.manager_to_viewer_pipe = None

        if self.viewer_to_manager_pipe:
            self.viewer_to_manager_pipe.close_all()

        self.viewer_to_manager_pipe = None

    @property
    def is_viewer_running(self) -> bool:

        return self._is_viewer_running


class GitExecutor:

    def __init__(self):

        self.full_path_to_target_dir: Optional[str] = None

    def set_git_directory(self, full_path_to_target_dir: str):

        self.full_path_to_target_dir: str = full_path_to_target_dir

    def update_remote_metadata(self) -> bool:
        self.run_git(["fetch"])
        return True

    def pull(self) -> bool:
        self.run_git(["pull"])
        return True

    def get_local_head_commit_hash(self) -> str:
        return self.run_git(["rev-parse", "HEAD"])

    def get_remote_head_commit_hash(self) -> str:
        return self.run_git(["rev-parse", "@{u}"])

    def run_git(self, args) -> str:

        """Helper to run a git command inside the repository directory."""

        # setup the GIT_ASKPASS environment variable to point to the AskPass.py script - which will supply the
        # credentials
        git_env: dict[str, str] = os.environ.copy()

        this_script_directory: Path = Path(__file__).parent.resolve()
        git_env["GIT_ASKPASS"] = os.path.join(this_script_directory, "AskPass.py")

        res = subprocess.run(
            ["git"] + args,
            cwd=self.full_path_to_target_dir,
            capture_output=True,
            text=True,
            check=True,
            env=git_env)

        return res.stdout.strip()


class UpdateManager:

    def __init__(self):

        self.git_executor: GitExecutor = GitExecutor()
        self.git_executor.set_git_directory(Configuration.get_config().get_viewer_directory())

    def is_update_available(self) -> bool:

        # do a fetch to update local metadata of remote repository
        self.git_executor.update_remote_metadata()

        local_head_hash: str = self.git_executor.get_local_head_commit_hash()
        remote_head_hash: str = self.git_executor.get_remote_head_commit_hash()

        return local_head_hash != remote_head_hash

    def perform_update(self) -> bool:

        self.git_executor.pull()
        return True


class Cycler:

    def __init__(self):

        self.update_manager: UpdateManager = UpdateManager()
        self.picture_viewer_manager: PictureViewerManager = PictureViewerManager()

    def on_run(self):
        """
        Intended to be invoked exactly once during the process cycle. Sleeps and monitors action conditions and end
        conditions
        """

        self.picture_viewer_manager.launch_viewer_as_process()

        while True:

            if self.update_manager.is_update_available():

                if self.picture_viewer_manager.is_viewer_running:
                    self.picture_viewer_manager.stop_viewer()

                self.update_manager.perform_update()

                self.picture_viewer_manager.launch_viewer_as_process()

            time.sleep(THIRTY_MINUTES_IN_SECONDS)


if __name__ == '__main__':

    # initialize configuration
    Configuration.do_standard_initialization()

    cycler: Cycler = Cycler()
    cycler.on_run()
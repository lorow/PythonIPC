import os
import tempfile
from contextlib import contextmanager


def write_to_pipe(pipe, data):
    """helper function for writing data to the pipes"""
    try:
        pipe.write(data + "\n")
    except Exception:
        print("Error wiring to pipe")


def read_from_pipe(pipe):
    try:
        return pipe.readline().rstrip()
    except Exception:
        return None


@contextmanager
def get_pipe(pipe_name):
    """helper function for creating named pipes"""
    pipe = None
    temporary_directory = tempfile.mkdtemp()
    filename = os.path.join(temporary_directory, pipe_name)
    try:
        os.mkfifo(filename)
        pipe = open(filename, "w+")
        yield pipe
    except Exception:
        print("Could not create named pipe: ", pipe_name)
    finally:
        __cleanup(pipe, file_name=filename, tmp_dir_path=temporary_directory)


def __cleanup(pipe, file_name, tmp_dir_path):
    if not pipe:
        return
    pipe.close()
    os.remove(file_name)
    os.rmdir(tmp_dir_path)

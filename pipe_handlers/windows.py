from contextlib import contextmanager

import pywintypes
import win32file
import win32pipe


def write_to_pipe(pipe, data):
    """helper function for writing data to the pipes"""
    try:
        win32file.WriteFile(pipe, bytes(data, "utf-8"))
    except pywintypes.error:
        print("Error wiring to pipe")


def read_from_pipe(pipe):
    try:
        _, data = win32file.ReadFile(pipe, 64 * 1024)
        return data
    except pywintypes.error:
        return None


@contextmanager
def get_pipe(pipe_name):
    """helper function for creating named pipes"""
    pipe = None
    try:
        pipe = win32pipe.CreateNamedPipe(
            rf"\\.\pipe\{pipe_name}",
            win32pipe.PIPE_ACCESS_DUPLEX,
            win32pipe.PIPE_TYPE_MESSAGE
            | win32pipe.PIPE_READMODE_MESSAGE
            | win32pipe.PIPE_WAIT,
            1,
            65536,
            65536,
            0,
            None,
        )
        win32pipe.ConnectNamedPipe(pipe, None)
        yield pipe
    except pywintypes.error:
        print("Could not create named pipe: ", pipe_name)
    finally:
        __cleanup(pipe)


def __cleanup(pipe):
    if not pipe:
        return
    win32pipe.DisconnectNamedPipe(pipe)
    win32file.CloseHandle(pipe)

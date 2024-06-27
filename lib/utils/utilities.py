from sys import _getframe
from os.path import join as path_join, isdir
from os import makedirs

def _create_dir(path_file: str|list) -> str:
    """
    Create dir(s)
    Params
    ----------
    path_file: List or str of the name of folder(s)
    to create or check if exist
    Return
    ----------
    str: path of the folder
    """
    file_path = _getframe(1).f_locals['self'].__class__.__module__.split(".")[:-1]
    file_path = "/".join(file_path)
    if type(path_file) == list:
        for path in path_file:
            file_path = path_join(file_path, path)
    elif type(path_file) == str:
            file_path = path_join(file_path, path_file)
    if isdir(file_path) == False:
        makedirs(file_path)
    return file_path

#def _save_source_code(filename: str = "source_code", source_code: str, output_dir: str) -> None:
def save_source_code(source_code: str, filename: str = "source_code") -> None:
    """
    Save the source code of the current page to a file
    Params
    ----------
    Required
        source_code: Content of the web page
    Optional
        filename: Filename of the source code file
    """
    with open(f"{filename}.html",
                "w", encoding = "utf-8") as tf:
        tf.write(source_code)
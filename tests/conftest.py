from testfixtures import TempDirectory
import pytest


@pytest.fixture
def temp_folder_and_files():
    import tempfile

    with tempfile.TemporaryDirectory() as tempdirname:
        open(f"{tempdirname}/file1", "w")
        open(f"{tempdirname}/file2", "w")
        open(f"{tempdirname}/file3", "w")

        yield tempdirname


@pytest.fixture()
def tempdir():
    with TempDirectory() as tempdir:
        yield tempdir

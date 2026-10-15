
import pytest


# Take an extra argument for pytest to set the location of the mmif-storage
# repository.
#
# With the newly introduced use of the example shack this now appears to be
# deprecated, but keeping it here for now.

# See:
# - https://stackoverflow.com/a/55301318
# - https://docs.pytest.org/en/7.1.x/example/simple.html

def pytest_addoption(parser):
    parser.addoption(
        "--mmif-storage-repo", action="store",
        help='the location of the mmif-storage repository')

@pytest.fixture(scope="session")
def mmif_storage_repo(pytestconfig):
    return pytestconfig.getoption("--mmif-storage-repo")

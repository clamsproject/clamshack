"""

Testing the ClamShack.

This has two requirements:

- A spacy-wrapper CLAMS app running in a container using port 5001. The spacy
  version used here is v2.3.
- A local copy of the mmif-storage repository. The tests assume that there is a
  mmif-storage repository as a sister to this repository, edit MMIF_STORAGE_REPO
  if it resides elsewhere.

TODO:
- The assumption above is a bit clunky. Should replace it with using the code in
  mmif_storage.create_example_storage() to avoid that dependency.

"""

import time
import shutil
from pathlib import Path

import pytest

import mmif_storage
from mmif_storage import StoragePath

from shack import ClamShack, ClamsApp, History, Job, ShackError


DEBUG = False
MMIF_STORAGE_REPO = '../mmif-storage'
ASSETS_FILE = 'tests/assets.txt'
APP_NAME = 'http://apps.clams.ai/spacy-wrapper/v2.3'
APP_URL = 'http://127.0.0.1:5001'


@pytest.fixture(scope='session')
def empty_shack(tmpdir_factory):
    tmpdir = tmpdir_factory.mktemp('shack')
    shack = ClamShack(f'{str(tmpdir)}/empty-shack', assets=ASSETS_FILE)
    yield shack


@pytest.fixture(scope='session')
def example_shack(tmpdir_factory, mmif_storage_repo):
    tmpdir = tmpdir_factory.mktemp('shack')
    repo = mmif_storage_repo
    if repo is None:
        repo = MMIF_STORAGE_REPO
    shack = ClamShack(f'{str(tmpdir)}/example-shack', assets=ASSETS_FILE)
    if DEBUG:
        print('\n>>> shack.location =', shack.location)
    mmif_dir_source = Path(repo) / 'src/mmif_storage/data/storage-example'
    mmif_dir_target = Path(str(tmpdir)) / 'example-shack/mmif'
    file_list = 'tests/storage-files.txt'
    copy_files(file_list, mmif_dir_source, mmif_dir_target)
    job1_file = shack.jobs_dir / 'j1-swt.txt'
    job2_file = shack.jobs_dir / 'j2-captioner.txt'
    job1_file.write_text(Path('tests/j1-swt.txt').read_text())
    job2_file.write_text(Path('tests/j2-captioner.txt').read_text())
    # With files added after creation we need to reload the shack so that it
    # initializes properly.
    shack = ClamShack(f'{str(tmpdir)}/example-shack', assets=None)
    yield shack


def copy_files(file_list: str, indir: str, outdir: str):
    """Copy a list of file paths in a file from one directory to the other,
    preserving the paths."""
    # NOTE. This was adapted from ../mmif_storage/tests/utils.py
    with open(file_list) as fh:
        for line in fh:
            line = line.strip()
            if line.startswith('#') or not line:
                continue
            f_in = Path(indir) / line.strip()
            f_out = Path(outdir) / line.strip()
            f_out.parent.mkdir(parents=True, exist_ok=True)
            f_out.write_text(f_in.read_text())


class TestBasics():

    """Test some basic functionality on an empty shack."""

    def test_create_clamshack(self, empty_shack: ClamShack, monkeypatch):
        """A new ClamShack creates its expected directory structure."""
        # Avoid loading or invoking a real CLAMS application during construction, this
        # is not needed for this test but maybe for some other future tests.
        # monkeypatch.setattr("shack.run.APPS", {})
        assert empty_shack.name == 'empty-shack'
        assert empty_shack.assets_dir.is_dir()
        assert empty_shack.mmif_dir.is_dir()
        assert empty_shack.sources_dir.is_dir()
        assert empty_shack.jobs_dir.is_dir()
        assert empty_shack.assets_file.is_file()
        assert empty_shack.history_file.is_file()
        assert empty_shack.queue_file.is_file()
        assert empty_shack.error_file.is_file()
        assert empty_shack.cwd() == Path(".")

    def test_is_clams_directory(self, empty_shack: ClamShack):
        assert empty_shack.is_clams_directory()
        empty_shack.mmif_dir.rmdir()
        assert not empty_shack.is_clams_directory()
        empty_shack.mmif_dir.mkdir()
        assert empty_shack.is_clams_directory()

    def test_cd_into_existing_directory(self, empty_shack: ClamShack):
        (empty_shack.mmif_dir / "first").mkdir()
        assert empty_shack.cd("first") == "first"
        assert empty_shack.cwd() == Path("first")
        assert empty_shack.cd("..") == "."
        assert empty_shack.cwd() == Path(".")
        (empty_shack.mmif_dir / "first").rmdir()

    def test_cd_raises_for_missing_directory(self, empty_shack: ClamShack):
        with pytest.raises(ShackError, match="does not exist"):
            empty_shack.cd("missing")

    def test_history_persists_commands(self, empty_shack: ClamShack):
        history = History(empty_shack.history_file)
        assert len(history) == 0
        history.add("pwd")
        history.add("ls")
        assert len(history) == 2
        assert history.data == ["pwd", "ls"]
        assert history.index == {1: "pwd", 2: "ls"}
        reloaded = History(empty_shack.history_file)
        assert reloaded.data == ["pwd", "ls"]
        history.reset()
        assert len(history) == 0
        assert empty_shack.history_file.read_text() == ""

    def test_storage_path_properties(self, empty_shack: ClamShack):
        dummy_path = "dummy-app/v0.1/d41d8cd98f00b204e9800998ecf8427e/result.mmif"
        dummy_path_short = "dummy-app/v0.1/d41d8cd9/result.mmif"
        # Need to update the storage path on the mmif_storage package because it is
        # required when initializing the StoragePath instance.
        mmif_storage.config.MMIF_STORAGE_DIR = str(empty_shack.mmif_dir)
        storage_path = StoragePath(dummy_path)
        assert storage_path.rel_path == Path(dummy_path)
        assert storage_path.full_path == empty_shack.mmif_dir / dummy_path
        assert storage_path.name == "result.mmif"
        assert storage_path.stem == "result"
        assert storage_path.shortpathname == dummy_path_short

    def test_add_parameter_converts_value_to_string(self, empty_shack: ClamShack):
        #shack = ClamShack(str(shack_path / 'shack'), assets=None)
        empty_shack.add_parameter("threshold", 0.75)
        assert empty_shack.params == {"threshold": "0.75"}

    def test_parse_job_file(self, empty_shack: ClamShack):
        job_file = empty_shack.jobs_dir / "job-1.txt"
        job_file.write_text(
            "STARTED\t2026-01-01T10:00:00\n"
            "DONE\t2026-01-01T10:00:05\n"
            "COMMAND\tclams-run --app-name example-app --input input.mmif\n"
            "PROCESS_ID\t1234\n"
            "GUID\tguid-1\t2.4183\tSUCCES\n")
        job = Job(job_file)
        assert job.name == "job-1"
        assert job.app == "example-app"
        assert job.pid == "1234"
        assert job.command == [
            "clams-run", "--app-name", "example-app", "--input", "input.mmif"]
        assert job.guids == [["guid-1", "2.4183", "SUCCES"]]
        assert job.time_elapsed() == 5
        assert job.info_guids() == [("guid-1", "2.4183", "SUCCES")]

    def test_register_app(self, empty_shack: ClamShack):
        """This test is mostly to check whether spacy is running."""
        empty_shack.register(APP_URL)
        app = ClamsApp(name=APP_NAME, url=APP_URL)
        assert APP_NAME in empty_shack.apps
        assert app.metadata()['identifier'] == APP_NAME


class TestShack():

    """Testing some higher-level functionality on an example shack."""

    def test_settings(self, example_shack):
        settings = {k:v for k,v in example_shack.get_settings()}
        assert settings['jobs'] == 2
        assert settings['path'] == '.'
        assert settings['parameters'] == {}
        assert settings['clams_app'] == None
        assert settings['sources'] == 2

    def test_deep_dir(self, example_shack):
        dirs = example_shack.subdirs(deep=True)
        assert len(dirs) == 1
        assert len(dirs[0].parts) == 3
        assert dirs[0].parts[0] == 'swt-detection'
        assert dirs[0].parts[1] == 'v8.6'
        assert dirs[0].parts[2] == 'd41d8cd98f00b204e9800998ecf8427e'

    def test_search(self, example_shack):
        # TODO: add params search, maybe embedded in the test_run_job so that there
        # is a parameter to search on
        mmif_search_result = example_shack.search('clip1', 'mmif')
        app_search_result = example_shack.search('capt', 'app')
        identifiers = list(mmif_search_result.keys())
        assert len(identifiers) == 1
        assert 'cpb-aacip-f551104e446-clip1' in identifiers
        assert len(app_search_result) == 1
        assert len(Path(app_search_result[0]).parts) == 6
        assert 'smolvlm2-captioner' in Path(app_search_result[0]).parts

    def test_prepare_job(self, example_shack):
        """A typical way to run an app manually is to search for the input directory
        given an app name, cd into it, set the parameters and then register and
        select an application to run. This funciton is testing those steps."""
        app_search_result = example_shack.search('capt', 'app')
        example_shack.cd(app_search_result[0])
        example_shack.add_parameter('pretty', True)
        example_shack.register(APP_URL)
        example_shack.select_app(APP_NAME)
        settings = {k:v for k,v in example_shack.get_settings()}
        assert settings['clams_app'] == APP_NAME
        assert APP_NAME in example_shack.apps
        assert settings['parameters']['pretty'] == 'True'
        assert 'smolvlm2-captioner' in Path(settings['path']).parts

    def test_run_job(self, example_shack):
        created_path = (
            'swt-detection/v8.6/d41d8cd98f00b204e9800998ecf8427e'
            '/smolvlm2-captioner/v1.0/d41d8cd98f00b204e9800998ecf8427e'
            '/spacy-wrapper/v2.3/5fe49d06725497b274b6eaaf0fe0c5d2')
        created_path = 'spacy-wrapper/v2.3/5fe49d06725497b274b6eaaf0fe0c5d2'
        with pytest.raises(ShackError, match="does not exist"):
            example_shack.cd(created_path)
        example_shack.run_job('j3')
        # Sending input to the container and writing the result to storage is done
        # in a separate process, so we give it some time to finish up.
        time.sleep(2)
        # TODO: only one of the two files gets actually written, this seems like 
        # the old spacy issue but we used the new spacy-wrapper (v2.3).
        assert (example_shack.jobs_dir / 'j3.txt').is_file()
        example_shack.cd(created_path)
        assert Path('cpb-aacip-f551104e446-clip1.mmif') in example_shack.files()
        search_results = example_shack.search(['pretty=True'], 'params')
        assert len(search_results) == 1
        assert 'spacy-wrapper' in search_results[0].parts


def print_settings(shack: ClamShack):
    print()
    for k, v in shack.get_settings():
        print(f'{k}\n  {v}')


# The following were suggested by copilot and are for future reference, they are
# disabled for now, but the index does need testing.

def xtest_mmif_index_finds_mmif_files(tmp_path, monkeypatch):
    monkeypatch.setattr("shack.run.APPS", {})
    shack = ClamShack(str(tmp_path / "example"), assets=None)
    result_dir = shack.mmif_dir / "input" / "app" / "run"
    result_dir.mkdir(parents=True)
    (result_dir / "document.mmif").write_text("{}")
    shack.reindex()
    assert "document" in shack.index.data
    assert Path("input/app/run/document.mmif") in shack.index.data["document"]

def xtest_mmif_search_matches_file_stem(tmp_path, monkeypatch):
    monkeypatch.setattr("shack.run.APPS", {})
    shack = ClamShack(str(tmp_path / "example"), assets=None)
    result_dir = shack.mmif_dir / "input" / "app" / "run"
    result_dir.mkdir(parents=True)
    (result_dir / "document.mmif").write_text("{}")
    shack.reindex()
    results = shack.search("doc", "mmif")
    assert "document" in results
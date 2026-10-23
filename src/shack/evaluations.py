
# To make the type hints work, not needed starting with Python 3.14.
from __future__ import annotations

from pathlib import Path

from git import Repo, Tree, Blob

from shack import utils
from shack.config import TASKS
from shack import utils


class EvaluationRepository:

    """Class to give access to data in the annotation repository. All data are
    taken from the repository itself and not the checked out working directory.
    Many data are cached into memory for quick access and updated only when we
    start using another branch.

    path    --  a Path to the local directory of the repository
    repo    --  an instance of git.Repo for this repository
    branch  --  string indicating the selected branch
    root    --  the root tree for the selected branch
    readme  --  contents of the readme file

    Description of repository data:

    _branches
        a dictionary of branches, keys are branch names (strings) and values are
        instances of git.Head
    _batches
        a dictionary of batches, keys are batch names (strings) and values are
        instances of BatchFile
    _projects
        a dictionary of projects, keys are project names (strings) and values are
        instances of Project

    """

    # TODO: create a common super type for EvaluationRepository and AnnotationRepository

    def __init__(self, directory: str, branch='main'):
        self.path = Path(directory)
        self.repo = Repo(directory)
        self.branch = branch
        self.root = self.repo.heads[self.branch].commit.tree
        self.load()

    def load(self):
        self._load_readme()
        self._load_branches()
        self._load_tasks()

    def _load_readme(self):
        self.readme = read_text(self.root / 'README.md')

    def _load_branches(self):
        """Storing both the branches and their names."""
        self._branches = { str(branch): branch for branch in self.repo.branches }

    def _load_tasks(self):
        self._tasks = {}
        for tree in self.root.trees:
            tree_path = self.path / 'projects' / tree.name
            if tree.name in TASKS:
                self._tasks[tree.name] = Task(self, Path(tree.path), tree)

    def __str__(self):
        return (
            f'<{self.__class__.__name__} "{str(self.path)}" '
            f'branch={self.branch} tasks={len(self._tasks)}>')

    @property
    def branches(self) -> dict:
      return self._branches

    @property
    def branch_names(self) -> list[str]:
        return list(sorted([branch for branch in self._branches]))

    @property
    def tasks(self) -> list[Path]:
        return sorted(self._tasks.values())

    @property
    def task_names(self):
        return sorted(self._tasks.keys())

    def get_task(self, name: str) -> Task:
        """Retrieve a task from the tasks dictionary."""
        return self._tasks.get(name)

    def set_branch(self, branch_name: str):
        """Select a new branch and update the root tree and all previously
        loaded data. Print a warning if the branch does not exist."""
        if branch_name in self.branch_names:
            self.branch = branch_name
            self.root = self.repo.heads[branch_name].commit.tree
            self.load()
        else:
            print(f'Warning, there is no branch named "{branch_name}"')

    def checkout(self, branch: str):
        self.branch = branch
        self.branches[branch].checkout()
        self.root = self.repo.heads[branch].commit.tree
        self.load()

    def pp(self):
        print(f'\n{self}')
        print(f'\nSelected branch:\n    {self.repo.active_branch}')
        print('\nBatches:')
        for task in self._taskes:
            print('   ', task)
        print('\nProjects:')
        print()


class Task(utils.FileSystemNode):

    def __init__ (self, repo: Repository, path: Path, tree: Tree):
        super().__init__(path)
        self.repository = repo
        self.tree = tree
        self.load()

    def load(self):
        self._load_readme()
        self._load_evalscript()

    def _load_readme(self):
        try:
            self.readme = read_text(self.tree / 'README.md')
        except KeyError:
            self.readme = ''

    def _load_evalscript(self):
        self.script = read_text(self.tree / 'evaluate.py')

    def __str__(self):
        return f'<Task "{self.name}">'


def read_text(blob: Blob):
    """Read and return the text from a blob."""
    # TODO: this is also defined in annotations.py, refactor
    return blob.data_stream.read().decode("utf-8")

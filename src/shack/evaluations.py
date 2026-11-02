
# To make the type hints work, not needed starting with Python 3.14.
from __future__ import annotations

from pathlib import Path
import inspect
import importlib

from git import Repo, Tree, Blob

from shack.config import TASKS
from shack import utils


class EvaluationRepository(utils.Repository):

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

    def __init__(self, directory: str, branch='main'):
        super().__init__(directory, branch)
        self.load()

    def load(self):
        super().load()
        self._load_tasks()

    def _load_tasks(self):
        self._tasks = {}
        for tree in self.root.trees:
            tree_path = self.path / 'projects' / tree.name
            if tree.name in TASKS:
                self._tasks[tree.name] = Task(self, Path(tree.path), tree)

    def __str__(self):
        return (
            f'<{self.__class__.__name__} "{str(self.path)}" '
            f'branch="{self.branch}" tasks={len(self._tasks)}>')

    @property
    def tasks(self) -> list[Path]:
        return sorted(self._tasks.values())

    @property
    def task_names(self):
        return sorted(self._tasks.keys())

    def get_task(self, name: str) -> Task:
        """Retrieve a task from the tasks dictionary."""
        return self._tasks.get(name)

    def get_tasks(self) -> dict:
        return { n: t for n, t in enumerate(self.task_names) }

    def pp(self):
        print(f'\n{self}')
        print(f'\nSelected branch:\n    {self.repo.active_branch}')
        print('\nBatches:')
        for task in self._taskes:
            print('   ', task)
        print('\nProjects:')
        print()


class Task(utils.FileSystemNode):

    """A Task has access to Path for the task in the working directory as well
    as to the git.Tree node for that task. Also has access to the enclosing
    repository.

    The main tasks for this class are (1) provide basic information on the task,
    (2) give access to the evaluator class (to be used when adding evaluation
    capabilities to the shack), and (3) store a dictionary with evaluation task
    requirements like the kind of data required, this will later be put in the 
    evaluation repository.

    name        -  name of the task
    path        -  path of the task
    repository  -  an Instance of EvaluationRepository
    evaluator   -  the Evaluator class, as subclass of ClamsAAPBEvaluationTask
    readme      -  content of the task's readme file
    script      -  content of the task's evaluate.py file
    doc         -  docstring of the evaluator class

    The gold_specifications class variable stores requirements for annotation
    data, for now this enumerates the relevant annotation projects, the format
    of the annotation files and the kinds of data that need to be in the
    annotations. The annotation projects will be removed at some point because
    technically they are not needed if you know what data should be in the
    annotations.

    """

    gold_specifications = {

        # Would like to add 'understanding-chyrons' and 'understanding-slates',
        # but those data are in json, what would be needed is (1) update the
        # evaluator so it can also load JSON and (2) interpret the format
        # specification as a disjunction (that is, make it a list).
        "TimePointLabeling": {
            # TODO: want to use '*-label' instead of 'scene-label' but cannot do
            # that until the matching code is refined
            'projects': ['scene-recognition'],
            'format': 'csv',
            'fields': ['at', 'scene-label']},
        
        "TimeFrameLabeling": {
            'projects': ['january-slates', 'newshour-chyrons', 'spoken-lid'],
            'format': 'csv',
            'fields': ['start', 'end', 'scene-label']}
    }

    def __init__ (self, repo: EvaluationRepository, path: Path, tree: Tree):
        super().__init__(path)
        self.repository = repo
        self.tree = tree
        self.load()

    def load(self):
        self._load_readme()
        self._load_evalscript()
        self._load_evaluator()

    def _load_readme(self):
        try:
            self.readme = utils.read_text(self.tree / 'README.md')
        except KeyError:
            self.readme = ''

    def _load_evalscript(self):
        self.script = utils.read_text(self.tree / 'evaluate.py')

    def _load_evaluator(self):
        """Load the evaluator class and put its doc string in the doc variable."""
        eval_module = importlib.import_module(f'{self.path.name}.evaluate')
        eval_class = getattr(eval_module, f'{self.path.name}Evaluator')
        self.evaluator = eval_class
        self.doc = self.evaluator.__doc__

    def __str__(self):
        return f'<Task "{self.name}">'

    @property
    def goldspec(self):
        return self.__class__.gold_specifications.get(self.name)

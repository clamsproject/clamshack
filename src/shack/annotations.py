"""

Module that takes care of any interactions with the aapb-annotations repository,
which is assumed to be somewhere on the local disk.

To use this hand the local directory of the checked out aapb-annotation repository
to the Repository class:

>>> Repository('PATH-TO_REPO')

The repository and the objects in it refer to the trees and blobs in the repository
as well as to the local paths in the working directory. But typically requested data
are retrieved from the trees and blobs, not from the local paths.

"""

# TODO:
#
# - Maybe allow for users who do not want to do a git-clone for the annotations
#   reporitory, using "Repo.clone_from(repo_url, local_dir)"
# - Not all batch comments follow the convention that comments are separated by
#   lines with dashes, maybe update the code so that file-initial sequences of
#   python comments are recognized as well.


# To make the type hints work, not needed starting with Python 3.14.
from __future__ import annotations

import os
import re
import json
from io import StringIO
from pathlib import Path
from collections import namedtuple

from git import Repo, Tree, Blob

from shack import utils


Comparison = namedtuple('Comparison', ['in_both', 'in_first', 'in_second'])


# TODO: add GoldFile class (similar to Batch, which is a single file)
# TODO: rename Batch into BatchFile
# TODO: introduce RepoFile as super of GOld and Batch


class Repository:

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
        self.path = Path(directory)
        self.repo = Repo(directory)
        self.branch = branch
        self.root = self.repo.heads[self.branch].commit.tree
        self.load()

    def load(self):
        self._load_readme()
        self._load_branches()
        self._load_batches()
        self._load_projects()

    def _load_readme(self):
        self.readme = read_text(self.root / 'README.md')

    def _load_branches(self):
        """Storing both the branches and their names."""
        self._branches = { str(branch): branch for branch in self.repo.branches }

    def _load_batches(self):
        self._batches = {}
        blobs = [b for b in (self.root / 'batches').blobs]
        for blob in blobs:
            if blob.name.endswith('.txt'):
                batches_path = self.path / 'batches' / blob.name
                self._batches[batches_path.stem] = BatchFile(batches_path, blob)

    def _load_projects(self):
        self._projects = {}
        trees = [t for t in (self.root / 'projects').trees]
        for tree in trees:
            tree_path = self.path / 'projects' / tree.name
            self._projects[tree.name] = Project(self, tree_path, tree)
 
    def __str__(self):
        return (
            f'<{self.__class__.__name__} "{self.path.name}" '
            f'branch={self.branch} projects={len(self._projects)}>')

    @property
    def branches(self) -> dict:
      return self._branches

    @property
    def branch_names(self) -> list[str]:
        return list(sorted([branch for branch in self._branches]))
   
    @property
    def batches(self) -> list[Batch]:
        return sorted(self._batches.values())

    @property
    def batch_names(self) -> list[str]:
        return sorted(self._batches.keys())

    @property
    def projects(self) -> list[Project]:
        return sorted(self._projects.values())

    @property
    def project_names(self):
        return sorted(self._projects.keys())

    def get_batch(self, name: str) -> Batch:
        """Retrieve a batch from the batches dictionary."""
        return self._batches[name]

    def get_project(self, name: str) -> Project:
        """Retrieve a roject from the projects dictionary."""
        return self._projects[name]

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
        for batch in self._batches:
            print('   ', batch)
        print('\nProjects:')
        for project in self._projects:
            print('   ', project)
        print()


class Project(utils.FileSystemNode):

    """An annotation project within the Repository

    name        --  inherited from FileSystemNode
    path        --  inherited from FileSystemNode
    repository  --  the Repository that the project is in
    tree        --  the Tree in the git.Repo where the project lives
    readme
    process

    _golds 
        a dictionary of gold files, keys are gold file names (strings) and values
        are instances of GoldFile
    _drops
        a dictionary of data drops, keys are data drop names (strings) and values
        are instances of DataDrop

    """

    def __init__ (self, repo: Repository, path: Path, tree: Tree):
        super().__init__(path)
        self.repository = repo
        self.path = path
        self.tree = tree
        self.name = tree.name
        self.load()

    def load(self):
        """Loads the README.md and process.py files as well as the list of gold
        files and the files in each data drop. Does not load the oother top-level
        files in the project."""
        self._load_readme()
        self._load_process()
        self._load_golds()
        self._load_drops()

    def _load_readme(self):
        self.readme = read_text(self.tree / 'README.md')

    def _load_process(self):
        try:
            self.process = read_text(self.tree / 'process.py')
        except KeyError:
            self.process = None

    def _load_golds(self):
        self._golds = {}
        try:
            for blob in (self.tree / 'golds').blobs:
                path = Path(blob.path)
                self._golds[path.stem] = GoldFile(path, blob)
        except KeyError:
            pass

    def _load_drops(self):
        self._drops = {}
        for tree in self.tree.trees:
            if tree.name != 'golds':
                path = self.repository.path / tree.path
                self._drops[tree.name] = DataDrop(self.repository, self, path, tree)

    @property
    def golds(self):
        return list(self._golds.values())

    @property
    def gold_names(self):
        return list(sorted(self._golds))

    @property
    def drops(self):
        return list(sorted(self._drops.values()))

    @property
    def drop_names(self):
        return list(sorted(self._drops))

    def __str__(self):
        return (
            f'<Project "{self.name}"'
            f' golds={len(self.golds)}'
            f' datadrops={len(self._drops)}>')

    def __eq__(self, other):
        return self.name == other.name

    def __lt__(self, other):
        return self.name < other.name

    def get_gold_file(self, filename: str):
        return self._golds.get(filename)

    def gold_file_content(self, filename: str):
        print('---',filename)
        return read_text(self.get_gold_file(filename))

    '''
    Some methods that were defined in the old Task class and that may be relevant
    here.

    @property
    def gold_files(self):
        if self._gold_files is None:
            self._gold_files = []
            if self._gold_directory.is_dir():
                for path in sorted(self._gold_directory.iterdir()):
                    if path.is_file():
                        self._gold_files.append(path)
                    else:
                        for subpath in sorted(path.iterdir()):
                            self._gold_files.append(subpath)
        return self._gold_files
    
    def process_content(self):
        if self.process_file.is_file():
            with self.process_file.open() as fh:
                return fh.read()
        return ''

    def gold_file_ids(self):
        return [f.stem for f in self.gold_files]

    def data_drop(self, data_drop: str):
        return self.data_drops.get(data_drop)

    def compare_to_batch(self, batch: Batch):
        gold_files = set(self.gold_file_ids())
        batch_files = set(batch.files)
        return Comparison(
            len(gold_files.intersection(batch_files)),
            len(gold_files.difference(batch_files)),
            len(batch_files.difference(gold_files)))
    '''


class DataDrop(utils.FileSystemNode):

    """A DataDrop contains the annotations results, each project can have multiple
    rounds of annotation.

    repository  --  the Repository that the dat adrop is in
    project     --  the Project that the data drop is for
    path        --  the Path in the working directory
    tree        --  the tree in the git.Repo instance

    _files
        a dictionary of files, keys are file names and values are instances of
        git.Blob

    """

    def __init__(self, repo: Repository, project: Project, path: Path, tree: Tree):
        super().__init__(path)
        self.repository = repo
        self.project = project
        self.path = path
        self.tree = tree
        self._files = { Path(b.name).stem: b for b in tree.blobs }

    @property
    def files(self):
        return list(self._files.values())

    @property
    def file_names(self):
        return list(sorted(self._files))

    def __len__(self):
        return len(self._files)

    def __str__(self):
        return f'<{self.__class__.__name__} {self.name} files={len(self)}>'

    def __contains__(self, element):
        return element in self._files

    def get_file(self, filename: str):
        return self._files.get(filename)

    def file_content(self, filename: str):
        return read_text(self.get_file(filename))


class RepoFile(utils.FileSystemNode):

    """A file in the repository

    name     --  inherited from FileSystemNode 
    path     --  inherited from FileSystemNode
    blob     --  the blob in the repository
    content  --  the full content of the batch file
    files    --  a list of files included in the batch file
    comment  --  the comment of the batch file
    
    """

    def __init__(self, path: Path, blob: Blob):
        super().__init__(path)
        self.blob = blob
        self._content = None

    @property
    def content(self):
        if self._content is None:
            self._content = read_text(self.blob)
        return self._content


class BatchFile(RepoFile):

    """Stores the content of a batch file.

    name     --  inherited from FileSystemNode 
    path     --  inherited from FileSystemNode
    blob     --  inherited from RepoFile
    content  --  inherited from RepoFile
    files    --  a list of files included in the batch file
    comment  --  the comment of the batch file
    
    """

    def __init__(self, path: Path, blob: Blob):
        super().__init__(path, blob)
        self.files = [l.strip() for l in self.content.splitlines()
                      if not l.strip().startswith('#')]
        self._comment = None

    def __str__(self):
        return f'<BatchFile {self.name} files={len(self)}>'

    def __len__(self):
        return len(self.files)

    @property
    def comment(self):
        # This uses the convention that comments start the file and start and end
        # with a line of at least dashes.
        if self._comment is None:
            comment = StringIO()
            separator_count = 0
            lines = self.content.split('\n')
            for line in lines:
                if '-' * 50 in line:
                    separator_count += 1
                    if separator_count == 2:
                        break
                    else:
                        continue
                if not line.startswith('#'):
                    break
                line = line.lstrip('#').strip()
                line = '\n' if not line else line
                comment.write(f'{line}\n')
            self._comment = comment.getvalue()
            #print(f'COMMENT:\n{self._comment}<<<')
        return self._comment

    def pp(self):
        print(f'\n{b}\n\n{b.content[:500]}\n')


class GoldFile(utils.FileSystemNode):

    """Stores the content of a gold file.

    name     --  inherited from FileSystemNode 
    path     --  inherited from FileSystemNode
    blob     --  inherited from RepoFile
    content  --  inherited from RepoFile
    
    """

    def __init__(self, path: Path, blob: Blob):
        super().__init__(path)
        self.path = path
        self.blob = blob
        self._content = None
    
    def __str__(self):
        return f'<GoldFile {self.name}>'

    @property
    def content(self):
        if self._content is None:
            self._content = read_text(self.blob)
        return self._content

    def pp(self):
        print(f'\n{b}\n\n{b.content[:500]}\n')


def read_text(blob: Blob):
    """Read and return the text from a blob."""
    return blob.data_stream.read().decode("utf-8")


def pp_tree(tree: Tree):
    print(f'{tree.name}/')
    for tree in tree.trees:
        print(f'    {tree.name}/')
    for blob in tree.blobs:
        print(f'    {blob.name}')

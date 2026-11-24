import csv
import json
import textwrap
import traceback
from cmd import Cmd
from pathlib import Path
import argparse
import inspect

from rich import box, prompt
from rich.panel import Panel
from rich.table import Table, Column
from rich.text import Text
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.style import Style

from mmif.utils.cli import describe
from mmif.utils.workflow_helper import describe_single_mmif
from mmif_storage.utils import load_json

from shack import ClamShack, ShackError, AlreadyDoneWarning
from shack.annotations import AnnotationRepository, Project, BatchFile
from shack.evaluations import EvaluationRepository, Task
from shack.config import messages, COMMANDS, SHELL_COMMANDS, ESHELL_COMMANDS
from shack.utils import console, timestamp, path_as_string
from shack.utils import info, warning, error, dribble, get_tree


DEBUG = False


def print_command(cmd: str):
    console.print(Text(cmd, "bold dark_blue"))


def print_help(command: str, description: str):
    lines = textwrap.wrap(
        description, width=80, initial_indent='     ', subsequent_indent='     ')
    text = Text.assemble('\n ', (command, "bold dark_blue"))
    console.print(text)
    for l in lines:
        console.print(l)


def print_exception(e: Exception):
    """Print the traceback to the console. Should be called only when dabbling
    with the Python capabilities of the shell, when a user fully deserves to be
    slammed by the full Python exception handdling."""
    for l in traceback.format_exception(e):
        print(l, end='')


class AbstractShell(Cmd):

    """Class to define the defaults for both the Shell and AnnotationShell. This
    is not an abstract class along the lines of the ABC module."""

    # Hidden commands are not advertized to the user when they type 'help'
    hidden_commands = {'s', 't', 'u', 'v', 'w', 'x', 'y', 'z', 'nl', 'echo', 'test'}

    def __init__(self):
        super().__init__()
        # The session log stores commands used and indicates when errors occurred,
        # the errors list is for errors encountered during the current session.
        self.log = []
        self.errors = []

    def default(self, line):
        """This applies if no command was recognized."""
        # NOTE: a potential problem is that both shells now have the same defaults
        if line == 'c':
            pass
        elif line in ("q", "EOF"):
            self.do_quit(line)
            return True
        elif line == 'h' or line.startswith('h '):
            self.do_history(f'{line[1:].strip()}')
        elif line.startswith('!'):
            # Mimicking the linux way to execute a previous command.
            n = line[1:]
            if n.isdigit():
                command = self.shack.history.index[int(n)]
                #console.print(Panel(f'{line} --> {command}'))
                print(command)
                self.cmdqueue.append(command)
        elif line == 'shack' or line.startswith('shack.'):
            try:
                console.print(eval(f'self.{line}'))
            except Exception as e:
                print_exception(e)
        elif line == 'shell' or line.startswith('shell.'):
            try:
                # since we are in the shell replace shell with self
                line = f'self{line[5:]}'
                console.print(eval(line))
            except Exception as e:
                print_exception(e)
        elif line.startswith('p '):
            # This is not advertized but it is here to sneak in the possibility
            # to evaluate Python expressions.
            command = ' '.join(line.split()[1:])
            if command:
                try:
                    console.print(eval(command))
                except Exception as e:
                    print_exception(e)
        else:
            warning(f'Unknown command: {line.strip().split()[0]}')

    def postcmd(self, stop, line):
        """Print an empty line after a command is executed and put the command
        on the history list."""
        print()
        try:
            if not self.is_hidden_command(line.split()[0]):
                if not line.startswith('!'):
                    self.shack.history.add(line)
                    self.log.append(f'COMMAND: {line}')
        except IndexError:
            pass
        return stop

    def onecmd(self, line):
        """Wrapping all single commands in some error handling that deals with any
        unexpected errors. Known errors and warnings should be dealt with directly
        in the do_x() methods themselves."""
        try:
            return super().onecmd(line)
        except Exception as e:
            warning(
                'An unexpected error occured, type "show error" to see the last'
                ' error that occurred')
            current_error = {
                'command': line,
                'timestamp': timestamp(),
                'stacktrace': []}
            for l in traceback.format_exception(e):
                current_error['stacktrace'].append(l)
            self.log.append(f'ERROR: {line}')
            self.errors.append(current_error)
            with open(self.shack.error_file, 'a') as fh:
                fh.write(f'\n>>> ERROR')
                fh.write(f'\n>>> shell command  =  {line}')
                fh.write(f'\n>>> time stamp     =  {timestamp()}\n\n')
                for l in traceback.format_exception(e):
                    fh.write(l)

    def get_commands(self) -> list:
        funs = inspect.getmembers(self.__class__, predicate=inspect.isfunction)
        names = [name[3:] for name, method in funs if name .startswith('do_')]
        names = [n for n in names if not self.is_hidden_command(n)]
        return names

    def is_hidden_command(self, command: str):
        if command.startswith('t_'):
            return True
        if command.startswith('t') and command[1:].isnumeric():
            return True
        return command in self.__class__.hidden_commands

    def do_help(self, arg):
        classname = self.__class__.__name__
        if not arg:
            names = self.get_commands()
            console.print(Panel('Available commands'))
            for cmd in names:
                print_command(' ' + cmd)
            console.print('\n Type "help <command>" for help on a command')
        elif classname == 'Shell' and arg in SHELL_COMMANDS:
            print_help(*SHELL_COMMANDS.get(arg))
        elif classname == 'EvaluationShell' and arg in ESHELL_COMMANDS:
            print_help(*ESHELL_COMMANDS.get(arg))
        else:
            print(f'No help available for {arg}')

    def do_history(self, arg):
        if arg == 'reset':
            self.shack.history.reset()
            console.print('Command history was reset')
        else:
            console.print(Panel(
                'Command history for this shack, use !INT to rerun a command'))
            for n, command in self.shack.get_history():
                 print(f' {n:2d}  {command}')

    def show_error(self):
        if self.errors:
            print(
                f'\n >>> ERROR'
                f'\n >>> shell command  =  {self.errors[-1]["command"]}'
                f'\n >>> time stamp     =  {self.errors[-1]["timestamp"]}\n')
            for line in self.errors[-1]['stacktrace']:
                console.print(f' {line}', end='')

    def show_errors(self):
        for error in self.errors:
            console.print(f'\n ERROR ON COMMAND: {error["command"]}\n')
            for line in error['stacktrace']:
                console.print(f' {line}', end='')


class Shell(AbstractShell):

    """Shell for command-line access to the ClamShack."""

    intro = ('\nYou entered the CLAMS shell. Type "?" for a list of commands.\n')
    prompt = None

    @classmethod
    def set_prompt(cls, shack: ClamShack):
        cls.prompt = f'(🐚 {shack.name}) '

    def __init__(self, clamshack: ClamShack):
        super().__init__()
        self.shack = clamshack
        self.set_prompt(self.shack)
        # Each time we got a couple of directories from a search we save it so we can
        # use it in the goto command.
        self.saved_directories = {}
        # Content created by the EvaluationShell
        self.view = None

    def __str__(self):
        return f'<Shell on "{self.shack.name}">'

    def emptyline(self):
        """Override repeating the last command."""
        pass

    ## Core actions

    def do_quit(self, arg):
        """Exit the CLAM Shack"""
        print(messages['bye'])
        return True

    def do_show(self, arg):
        if arg == 'error':
            self.show_error()
        elif arg == 'errors':
            self.show_errors()
        else:
            table = Table(show_header=False)
            for name, value in self.shack.get_settings():
                #console.print(f' {name:10}  =  {value}')
                if name == 'path':
                    table.add_row(name, path_as_string(Path(value)))
                else:
                    table.add_row(name, str(value))
            console.print(Panel("Shack settings and information"))
            console.print(table)

    def do_search(self, arg):
        if not arg:
            warning('No search parameters given')
            return
        search_type, *args = arg.split()
        if search_type == 'assets':
            results = self.shack.search(term=args[0], mode='assets')
            console.print(Panel(f'Assets matching "{args[0]}"'))
            for r in results:
                print(f' {r.name}')
        elif search_type == 'mmif':
            results = self.shack.search(term=args[0], mode='mmif')
            console.print(Panel(f'MMIF files matching "{args[0]}"'
                                 ' and the directories where they occur'))
            for name in results:
                print(' ' + name)
                for p in results[name]:
                    print('    ', path_as_string(p.parent))
        elif search_type == 'app':
            results = self.shack.search(term=args[0], mode='app')
            console.print(Panel(f'Directories created by app matching "{args[0]}"'))
            self.saved_directories = {}
            for n, result in enumerate(results):
                self.saved_directories[n] = result
                print(f' {n:2d}: {path_as_string(result)}')
        elif search_type == 'params':
            try:
                results = self.shack.search(term=args, mode='params')
                search_params = ' & '.join(args)
                console.print(Panel(f'Directories created with parameter {search_params}'))
                self.saved_directories = {}
                for n, result in enumerate(results):
                    self.saved_directories[n] = result
                    print(f' {n:2d}: {path_as_string(result)}')
            except Exception as e:
                warning(e)
        else:
            warning(f'Cannot search for "{arg}", use "assets", "mmif" or "app"')
            return

    def do_apps(self, arg):
        app_dict = dict(enumerate(self.shack.app_names))
        if not arg:
            console.print(Panel('Registered CLAMS Apps'))
            for key in sorted(app_dict):
                console.print(f' {key}: {app_dict[key]}')
        else:
            selection = arg
            if selection.isnumeric():
                selection = app_dict.get(int(selection))
            succeeded = self.shack.select_app(selection)
            if succeeded:
                dribble(f'Selected {selection}')
            else:
                warning(f'Selection does not exist')

    def do_register(self, arg):
        result = self.shack.register(arg)
        print(result)

    def do_jobs(self, arg):
        if arg:
            try:
                job = self.shack.jobs[arg]
                console.print(Panel(job.name))
                info_table = Table('property', 'value', box=box.ROUNDED)
                for prop, val in job.info():
                    info_table.add_row(prop, val)
                console.print(info_table)
                info_guids_table = Table('guid', 'time', 'result', box=box.ROUNDED)
                for guid, t, result in job.info_guids():
                    info_guids_table.add_row(guid, t, result)
                console.print(info_guids_table)
            except KeyError:
                warning('No such job.')
                return
        else:
            console.print(Panel(
                'Jobs associated with this Shack'
                ' (listed in order of when they were started)'))
            table = Table('name', 'app', 'guids', 'status', 'time (s)', box=box.ROUNDED)
            for job in sorted(self.shack.jobs.values(), key=lambda x: x.started, reverse=False):
                status = 'done' if job.finished else 'running'
                elapsed = str(job.time_elapsed())
                table.add_row(job.name, job.app, str(len(job.guids)), status, elapsed)
            console.print(table)

    def do_params(self, arg):
        args = arg.split()
        if len(args) >= 1:
            if args[0] == 'reset':
                self.shack.params_file = None
                self.shack.params = {}
            # loading a file with "params @FILENAME"
            elif args[0].startswith('@'):
                fname = args[0][1:].strip()
                try:
                    params = load_json(fname)
                    self.shack.params = params
                    self.shack.params_file = fname
                except FileNotFoundError:
                    print(f'There is no file "{fname}"')
                except json.decoder.JSONDecodeError:
                    print(f'No valid JSON in {fname}')
            # setting a parameter with "params PARAM=VALUE"
            elif '=' in args[0]:
                param, value = args[0].split('=', 1)
                self.shack.add_parameter(param, value)
        console.print(self.shack.params)

    def do_run(self, arg):
        if not arg:
            warning('You must provide a name for the job.')
            return
        if self.shack.app is None:
            warning('You must select a CLAMS app.')
            return
        if arg in self.shack.jobs:
            warning('A job with that name already exists.')
            return
        if self.shack.cwd() != Path('.'):
            files = [Path(f.name) for f in self.shack.files() if f.suffix == '.mmif']
            if not files:
                print('Nothing to do, there are no MMIF files in the current path')
                return
        process_id = self.shack.run_job(arg)
        console.print(Panel('Started job'))
        dribble(f'  name   = {arg}')
        dribble(f'  path   = {path_as_string(self.shack.cwd())}')
        dribble(f'  app    = {self.shack.app}')
        dribble(f'  params = {self.shack.params}')
        dribble(f'  pid    = {process_id}')

    def do_index(self, arg):
        self.shack.reindex()
        print('Recreated the MMIF Index')

    def do_source(self, arg):
        """Loads a file of commands and then run them. The file of commands has to
        be in the same format as the file that is created by the "history save"
        command."""
        # TODO: check the source file so that it only has one run command
        if arg:
            script_path = Path(arg)
            if script_path.is_file():
                commands = []
                for line in script_path.read_text().split('\n'):
                    if line.strip() and not line.strip().startswith('#'):
                        commands.append(line.strip())
                for c in commands:
                    self.cmdqueue.append(f'echo {c}')
                    self.cmdqueue.append(c)
            else:
                warning(f'Script file "{arg}" is not a file')
        else:
            warning("You need to specify a script to source.")

    def do_pwd(self, arg):
        path = self.shack.cwd()
        if str(path) in ('', '.'):
            print('.')
        else:
            print('', path_as_string(path))

    def do_dirs(self, arg):
        if arg == '-s':
            if self.saved_directories:
                console.print(Panel(f'Last directories saved (using full storage path)'))
                for n, path in self.saved_directories.items():
                    print(f' {n:2d}: {path_as_string(path)}')
            else:
                print('\n No directories were saved.')
        elif arg == '-d':
            dirs = self.shack.subdirs(deep=True)
            p = path_as_string(self.shack.cwd())
            console.print(Panel(f'Expanded sub directories at "{p}"'))
            self.saved_directories = {}
            for n, (d1, d2) in enumerate(dirs):
                self.saved_directories[n] = d1
                print(f' {n:2d}: {path_as_string(d2)}')
        else:
            p = path_as_string(self.shack.cwd())
            console.print(Panel(f'Sub directories at "{p}"'))
            for n, d in enumerate(self.shack.subdirs()):
                print(f' {n:2d}: {str(d)}')

    def do_files(self, arg):
        console.print(Panel(f'MMIF files at "{path_as_string(self.shack.cwd())}"'))
        for n, f in enumerate(self.shack.files()):
            print(f' {n}: {str(f)}')

    def do_cd(self, arg):
        # first translate an index from the dir command into a sub directory
        subdirs = { n: str(p) for n, p in enumerate(self.shack.subdirs()) }
        if arg.isnumeric() and int(arg) in subdirs:
            arg = subdirs[int(arg)]
        try:
            new_path = self.shack.cd(arg)
            print(path_as_string(Path(new_path)))
        except ShackError as e:
            warning(e)

    def do_home(self, arg):
        self.do_cd('~')

    def do_up(self, arg):
        try:
            repetitions = int(arg) if arg else 1
            for i in range(repetitions):
                self.shack.cd('..')
            print(path_as_string(self.shack.path))
        except ValueError:
            warning('The argument can only be an integer')

    def do_tree(self, arg):
        args = arg.split()
        full = True if '-f' in args else False
        parameters = True if '-p' in args else False
        if '-v' in args:
            full = True
            parameters = True
        prefix = self.shack.mmif_dir
        t = get_tree(self.shack.mmif_dir / self.shack.path, prefix=prefix, full=full)
        console.print(Panel('MMIF File tree'))
        self.do_nl('')
        console.print(t)
        if parameters:
            parameter_file = self.shack.parameter_file()
            if parameter_file is not None:
                print()
                #console.print(Panel(path_as_string(parameter_file)))
                console.print(Panel('Parameters'))
                console.print(parameter_file.read_text())

    def do_goto(self, arg):
        try:
            self.shack.cd('~')
            directory = self.saved_directories.get(int(arg))
            if directory is None:
                warning('There is no saved directory at that index')
                return
            self.shack.cd(str(directory))
            #print(path_as_string(directory))
            self.do_tree('-p')
        except ValueError:
            warning('goto command requires an integer')

    def do_prune(self, arg):
        try:
            text = Text(
                f'\n Deleting {path_as_string(self.shack.cwd())}\n'
                + '\n This cannot be undone\n')
            text.stylize("bold red")
            console.print(text)
            answer = input(' Continue? (y/n) ')
            if answer == 'y':
                self.shack.prune()
            console.print(Panel(f' Deleted {path_as_string(self.shack.cwd())}'))
        except ShackError as e:
            warning(e)

    def do_view(self, arg):
        saved_path = self.shack.path
        if saved_path == '.':
            saved_path = '~'
        self.do_goto(arg)
        self.shack.cd('~')
        #self.do_view(arg)
        self.shack.cd(str(saved_path))
        
    def do_describe(self, arg):
        if not arg.isdigit():
            warning('The argument must be an integer')
            return
        full_path = self.shack.mmif_dir / self.shack.path
        for n, f in enumerate(self.shack.files()):
            if n == int(arg):
                if not (full_path / f).suffix == '.mmif':
                    warning('The file at that index is not a MMIF file')
                    return
                console.print(Panel(f'describe {str(f)}'))
                desc = describe_single_mmif(full_path / f)
                console.print(desc)
                return
        warning('No MMIF file at that index')

    def do_echo(self, arg):
        """Just a utility method to use in scripts, may be deprecated."""
        print(f'>>> {arg}')

    def do_nl(self, arg):
        # Utility command for when adding multiple commands to the queue, may be
        # deprecated.
        print()

    def do_eval(self, arg):
        self.view = EvaluationShell(self).cmdloop()
        # TODO: should save the view state, replacing ojects like the project with names
        print('Exited the annotation subshell')

    ## Undocumented actions for debugging and development, do not rely on the 
    ## continued presence of any of these.

    def do_s(self, arg):
        self.cmdqueue.append('source example-script.txt')

    def do_t(self, arg):
        self.cmdqueue.append('search app swt')
        self.cmdqueue.append('goto 0')
        self.cmdqueue.append('eval')

    def do_t2(self, arg):
        self.cmdqueue.append('search app whisper')
        self.cmdqueue.append('goto 0')
        self.cmdqueue.append('eval')

    def do_t3(self, arg):
        self.cmdqueue.append('cd 0')
        self.cmdqueue.append('eval')

    def do_test(self, arg):
        if arg == 'search':
            self.cmdqueue.append('search assets f55')
            self.cmdqueue.append('search mmif f55')
            self.cmdqueue.append('search app captioner')
            self.cmdqueue.append('search params pretty=True threshold=3')
            self.cmdqueue.append('view 0')
        elif arg == 'spacy':
            self.cmdqueue.append('register http://127.0.0.1:5001')
            self.cmdqueue.append('apps 0')
            self.cmdqueue.append('cd ~')
            self.cmdqueue.append('cd swt-detection/v8.6/d41d8cd98f00b204e9800998ecf8427e/smolvlm2-captioner/v1.0/d41d8cd98f00b204e9800998ecf8427e')
            self.cmdqueue.append('params @example-params.json')
            self.cmdqueue.append('run t1')
            self.cmdqueue.append('home')
        elif arg == 'misc':
            self.cmdqueue.append('show')
            self.cmdqueue.append('tree')
            self.cmdqueue.append('jobs')
        elif arg == 'dirs':
            self.cmdqueue.append('dirs')
            self.cmdqueue.append('dirs -d')
            self.cmdqueue.append('cd swt-detection/v8.6/d41d8cd98f00b204e9800998ecf8427e')
            self.cmdqueue.append('files')

    def do_x(self, arg):
        self.cmdqueue.append('register http://127.0.0.1:5001')
        self.cmdqueue.append('apps 0')
        self.cmdqueue.append('cd 0')
        self.cmdqueue.append('cd 0')
        self.cmdqueue.append('cd 0')
        self.cmdqueue.append('cd 0')
        self.cmdqueue.append('cd 0')
        self.cmdqueue.append('cd 0')
        self.cmdqueue.append('params pretty True')
        self.cmdqueue.append('params params.json')
        self.cmdqueue.append('jobs')
        self.cmdqueue.append('show')

    def do_y(self, arg):
        self.cmdqueue.append('register 127.0.0.1:5001')
        self.cmdqueue.append('apps')

    def do_z(self, arg):
        self.cmdqueue.append('source s.txt')

    def do_w(self, arg):
        self.cmdqueue.append('source s2.txt')


class EvaluationShell(AbstractShell):

    """A shell to help explore available annotations and gather information for
    down stream evaluations. Returns upon exit an AnnotationView with annotation
    state data."""

    intro = (
        '\nThis is the evaluation shell. With it you can select evaluation tasks, '
        'drill down into annotation projects and annotations batches, and then '
        'run and store evaluations.\n'
        '\nType help or ? for a list of commands.\n')

    # See https://www.unicode.org/emoji/charts/full-emoji-list.html for other 
    # emoji options. This one is number 1274, code point U+1F50E.
    prompt = '(🔎 eval) ' 

    def __init__(self, shell: Shell):
        super().__init__()
        self.parent = shell
        self.shack = shell.shack
        # Access to the annotations and evaluations repositories
        self.annotations = None
        self.evaluations = None
        # View on annotations and evaluations, will be returned on exit
        self.view = EvaluationView(self)

    def __str__(self):
        name1 = 'None' if self.annotations is None else self.annotations.path
        name2 = 'None' if self.evaluations is None else self.evaluations.path
        return f'<EvaluationShell on "{name1}" and "{name2}">'

    @property
    def annotations_path(self): 
        return '' if self.annotations is None else str(self.annotations.path)

    @property
    def evaluations_path(self):
        return '' if self.evaluations is None else str(self.evaluations.path)

    def preloop(self):
        pass

    def cmdloop(self, intro=None):
        """Override cmdloop to return the state value."""
        super().cmdloop(intro)
        return self.view

    def load_repositories(self):
        """Attempt to load annotation and evaluation repositories, checking for
        common locations."""
        # TODO: probably needs work once we run the shack from a command script
        for location in ('../aapb-annotations', '../aapb/aapb-annotations'):
            if Path(location).is_dir():
                self.load_annotations(location)
        for location in ('../aapb-evaluations', '../aapb/aapb-evaluations'):
            if Path(location).is_dir():
                self.load_evaluations(location)

    def load_annotations(self, location: str):
        """Load the annotations and give the view the full dictionaries of projects
        and batches.""" 
        self.annotations = AnnotationRepository(location)
        self.view.projects = self.annotations.get_projects()
        self.view.batches = self.annotations.get_batches()
        print(f' Loaded annotation repository in "{location}"')

    def load_evaluations(self, location: str):
        """Load the evaluations and give the view the full task dictionary."""
        self.evaluations = EvaluationRepository(location)
        self.view.tasks = self.evaluations.get_tasks()
        print(f' Loaded evaluation repository in "{location}"')

    def show_info(self):
        console.print(Panel("Evaluation shell settings"))
        console.print(f' shack location    - "{self.shack.location}"')
        console.print(f' shack path        - "{self.shack.path}"')
        console.print(f' annotations       - {self.annotations}')
        console.print(f' evaluations       - {self.evaluations}')
        console.print(f' selected task     - {self.view.task}')
        console.print(f' selected project  - {self.view.project}')
        console.print(f' selected batch    - {self.view.batch}')

    def show_project(self, args):
        if len(args) == 1:
            project = self.view.project
            header = "Readme file of current project"
        else:
            project_name = get_name(self.view.projects, args[1])
            project = self.annotations.get_project(project_name)
        if project is None:
            # see comment in show_task()
            warning(f'Project "{project_name}" does not exist')
        else:
            console.print(Panel(f'Project {project.name}'))
            #console.print(f' {self.view.project}')
            t = Table(show_header=False)
            t.add_row('golds', str(len(project.golds)))
            t.add_row('batches', str(len(project.batches)))
            specs = project.goldspec
            if specs is not None:
                t.add_row('format', specs['format'])
                t.add_row('fields', ' '.join(specs['fields']))
                console.print(t)
            if project.golds:
                selected_gold = project.golds[0]
                console.print(f'\n Example gold file: {selected_gold}')
                console.print(
                    Panel(selected_gold.get_content_sample(),
                          style="navy_blue", border_style="bold grey66"))

    def show_batch(self, args):
        if len(args) == 1:
            batch = self.view.batch
            header = 'Current batch'
        else:
            batch_name = get_name(self.view.batches, args[1])
            batch = self.annotations.get_batch(batch_name)
            header = f'Batch {batch_name}'
        console.print(Panel(header))
        console.print(f' {batch}')
        # see comment in show_task()
        if batch is not None:
            console.print(Panel(batch.comment))

    def show_task(self, args):
        if len(args) == 1:
            task = self.view.task
            if task is None:
                warning(f'No task selected')
                return
            header = "Readme file of current task"
        else:
            task_name = get_name(self.view.tasks, args[1])
            task = self.evaluations.get_task(task_name)
        if task is None:
            # TODO: this, and its siblings should allow for the case where
            # no task was selected (done for this one)
            warning(f'Task "{task_name}" does not exist')
        else:
            console.print(Panel(f'{task.name}'))
            console.print(' Evaluator class documentation', style='bold')
            # Markdown does not look very well in the shack so just dumping the
            # docstring in a panel
            console.print(Panel(task.doc))
            specs = task.goldspec
            table = Table(show_header=False)
            table.add_row('projects', ' '.join(specs['projects']))
            table.add_row('format', specs['format'])
            table.add_row('fields', ' '.join(specs['fields']))
            console.print(' Gold data specifications', style='bold')
            console.print(table)

    def select_project(self, identifier: str) -> Project:
        """Select a project, store it in the view and return it. The identifier
        can be a name like 'scene-recognition' or a key in the view's projects
        dictionary."""
        project_name = get_name(self.view.projects, identifier)
        project = self.annotations.get_project(project_name)
        self.view.project = project
        self.view.drops = list(sorted(project.drops))
        return project

    def select_batch(self, identifier: str) -> BatchFile:
        """Select a batch, store it in the view and return it. The identifier can be
        a name like 'scene-aapb-collaboration-27-a' or a key in the view's batches
        dictionary."""
        batch_name = get_name(self.view.batches, identifier)
        batch = self.annotations.get_batch(batch_name)
        self.view.batch = batch
        return batch

    def do_quit(self, arg):
        return True

    def do_show(self, arg):
        args = arg.split()
        if not arg:
            self.show_info()
        elif arg == 'error':
            self.show_error()
        elif arg == 'errors':
            self.show_errors()
        elif args[0] == 'project':
            self.show_project(args)
        elif args[0] == 'batch':
            self.show_batch(args)
        elif args[0] == 'task':
            self.show_task(args)
        # this option is not documented, for development only for now
        elif args[0] == 'task-script':
            if len(args) == 1:
                task = self.view.task
                header = "Readme file of current task"
            else:
                task_name = get_name(self.view.tasks, args[1])
                task = self.evaluations.get_task(task_name)
            if task is None:
                warning(f'Task "{task_name}" does not exist')
            else:
                console.print(Panel(f'{task} evaluate.py'))
                console.print(Syntax(task.script, 'python'))
        else:
            warning('Unexpected argument to "show"')
            self.do_help('show')

    def do_load(self, arg):
        """Load the annnotation or evaluation repository from the given directory.
        Assumes that the name of the location includes 'annotation' or 'evaluation'
        and uses that to determine what kind of repository is loaded."""
        if not arg:
            self.load_repositories()
        elif 'annotations' in arg:
            self.load_annotations(arg)
        elif 'evaluations' in arg:
            self.load_evaluations(arg)

    def do_branch(self, arg):
        args = arg.split()
        if len(args) == 2 and args[0] in ('annotations', 'evaluations'):
            repo = getattr(self, args[0])
            if repo is not None:
                result = repo.set_branch(args[1])
                if result:
                    print(f' Set branch in "{repo.path}" to {args[1]}"')
                    # When we have changed the branch we want to update the tasks,
                    # projects and batches on the view
                    if args[0] == 'annotations':
                        self.view.projects = self.annotations.get_projects()
                        self.view.batches = self.annotations.get_batches()
                    elif args[0] == 'evaluations':
                        self.view.projects = self.evaluations.get_tasks()
            else:
                print('Cannot set branch because repository is not loaded')
        else:
            warning('Unexpected argument to "branch"')
            self.do_help('branch')

    def do_projects(self, arg):
        if arg:
            # one argument means we are selecting a project
            project = self.select_project(arg)
            print(f' Selected project "{project.name}"')
        else:
            # no argument means we want a listing
            projects = self.view.projects
            if self.view.task is not None:
                # only keep the relevant projects for the task
                goldspec = self.view.task.goldspec
                project_specs = Project.gold_specifications
                matching_projects = Project.matching_projects(goldspec)
                projects = { 
                    identifier: name for identifier, name in projects.items()
                    if name in matching_projects }

            table = projects_table()
            for project_id, project_name in projects.items():
                project = self.annotations.get_project(project_name)
                gold_count = str(len(project._golds))
                batch_count = str(len(project._batches))
                specs = project.goldspec
                gold_format = '' if specs is None else specs.get('format', '')
                gold_fields = 0 if specs is None else len(specs.get('fields', []))
                table.add_row(
                    str(project_id), project_name, gold_format, str(gold_fields),
                    gold_count, batch_count)
            console.print(table)

    def do_batches(self, arg):
        if arg:
            # one argument means we are selecting a batch
            batch = self.select_batch(arg)
            print(f' Selected batch "{batch.name}"')
        else:
            batches = self.view.batches
            text = ('Full list of annotation batches, with number of files per '
                    'batch. A file can be annotated in multiple annotation tasks '
                    'but not every file in a batch has to be annotated. The last '
                    'column gives the overlap of the batch with the Shack files.')
            if self.view.project is not None:
                # only keep the batches that are included in the project
                project_batches = set(self.view.project.batches.keys())
                batches = {
                    identifier: name for identifier, name in batches.items()
                    if name in project_batches }
                text = ('List of annotation batches for this project, with '
                        'number of annotated files per batch.')
            identifiers = self.shack.identifiers
            # TODO: these should be removed
            #identifiers.append('cpb-aacip-0009a7e5474')
            #identifiers.append('cpb-aacip-507-930ns0mg7g')
            table = batches_table()
            for batch_id, batch_name in batches.items():
                batch_name = self.view.batches[batch_id]
                batch = self.annotations.get_batch(batch_name)
                overlap = str(len(batch.overlap(identifiers)))
                table.add_row(str(batch_id), batch.stem, str(len(batch.files)), overlap)
            print_panel_text_table('Annotation batches', text, table)

    def do_tasks(self, arg):
        if arg:
            task_name = arg
            tasks = self.view.tasks
            if arg.isnumeric() and int(arg) in tasks:
                task_name = tasks[int(arg)]
            task = self.evaluations.get_task(task_name)
            self.view.task = task
            print(f' Selected task "{task_name}"')
        else:
            # TODO: maybe print this as a table, like the batches (although in this
            # case ther eis no extra information to display).
            print_dictionary(self.view.tasks, 'Annotation tasks')

    def do_reset(self, arg):
        self.view.reset()

    def do_run(self, arg):
        """Run an evaluation. First ask the shack to run the evaluation and save
        all evaluation data. Then display a summary of the results."""
        try:
            evaluator = self.shack.run_eval(self.annotations, self.view)
            results_json = json.loads(evaluator.write_results())
        except AlreadyDoneWarning as e:
            warning('Already ran this evaluation, showing previously computed results')
            results = Path(e.results_directory) / 'eval-results.json'
            results_json = json.loads(results.read_text())
        # Print a table with the results
        console.print(Panel('Evaluation report'))
        eval_path = f'{self.view.task.name}/{self.view.project.name}/{self.view.batch.name}'
        console.print(f' CLAMS app output    -  "{self.view.path}"')
        console.print(f' task/project/batch  -  "{eval_path}"')
        print_results(results_json)


    ## Undocumented actions for debugging and development, do not rely on the
    ## continued presence of any of these.

    def do_t(self, arg):
        self.do_load('../aapb/aapb-annotations')
        self.do_load('../aapb/aapb-evaluations')
        self.do_tasks('TimePointLabeling')
        self.do_projects('scene-recognition')
        self.do_batches('aapb-collaboration-27-a')
        self.do_show('')

    def do_t2(self, arg):
        self.do_load('../aapb/aapb-annotations')
        self.do_load('../aapb/aapb-evaluations')
        self.do_branch('annotations 130-lid')
        self.do_tasks('TimeFrameLabeling')
        self.do_projects('spoken-lid')
        self.do_batches('mellon-slid-a')
        self.do_show('')

    def do_t3(self, arg):
        self.do_show('')


class EvaluationView():

    """This is the current view on the annotation and evaluation repositories. It
    data relevant to the evaluation shell. In particular, this class stores the
    the selected evaluation task, annotaton project and batch.

    task      --  an instance of Task
    project   --  an instance of Project
    batch     --  an instance of BatchFile

    tasks
        a dictionary mapping indices to task names, this will only when new evaluation
        tasks are added to the code base
        entire session
    projects
        a dictionary mapping indices to project names, will change depending on what
        task is selected
    batches
        a dictionary mapping indices to batch names, will change depending on what
        task and project are selected

    """

    def __init__(self, shell: EvaluationShell):
        self.shell = shell
        self._path = shell.shack.path
        self._task = None
        self._project = None
        self._batch = None
        self.tasks = {}
        self.projects = {}
        self.batches = {}

    @property
    def path(self):
        return self._path

    @property
    def task(self):
        return self._task

    @task.setter
    def task(self, value: Task):
        if not isinstance(value, Task):
            raise TypeError(f'{value} is not of type evaluations.Task')
        # Project and batch selection is reset when changing the task, but only 
        # do that when we are really changing the task.
        # TODO: should this also update the projects and batches dictionaries?
        if value is not self.task:
            self._task = value
            self._project = None
            self._batch = None

    @property
    def project(self):
        return self._project

    @project.setter
    def project(self, value: Project):
        if not isinstance(value, Project):
            raise TypeError(f'{value} is not of type annotations.Project')
        # Batch selection is reset when changing the project, but only do that
        # when we are really changing the project.
        if value is not self.project:
            self._project = value
            self._batch = None

    @property
    def batch(self):
        return self._batch

    @batch.setter
    def batch(self, value):
        self._batch = value

    @property
    def batch_name(self):
        return '' if self.batch is None else self.batch.name        

    @property
    def project_name(self):
        return '' if self.project is None else self.project.name        

    def as_table(self):
        # TODO: hook this up with the EvaluationShell.do_show() method
        return [
            ('selected project', self.project),
            ('selected batch', self.batch),
            ('selected task', self.task)]

    def as_json(self):
        return {}

    def set_task(self, task):
        pass

    def reset(self):
        """Reset the selected project, batch and task."""
        # using the hidden variables to bypass the type checking of the setters
        self._task = None
        self._project = None
        self._batch = None


def get_name(view_dictionary, name: str):
    if name.isnumeric() and int(name) in view_dictionary:
        name = view_dictionary[int(name)]
    return name


def get_measure(measures: dict, measure: str):
    """Return a precision, recall or fscore measure from a dictionary and make
    it a string for the sake of putting it in a rich Table. Turn None values
    into NaN."""
    val = measures[measure]
    return 'NaN' if val is None else f'{val:3.2f}'


def print_results(results_json: dict):
    table = results_table()
    vals = {}
    for prop, values in results_json.items():
        if prop[-2:] in ('_P', '_R', '_F'):
            measure = prop[-1]
            label = prop[:-2]
            if label not in vals:
                vals[label] = {'P': None, 'R': None, 'F': None}
            vals[label][measure] = values['0']
    for label, measures in vals.items():
        precision = get_measure(measures, 'P')
        recall = get_measure(measures, 'R')
        fscore = get_measure(measures, 'F')
        table.add_row(label, precision, recall, fscore)
    console.print(table)


def projects_table() -> Table:
    table = Table(
        Column(header='id', justify='right'),
        'project',
        'format',
        Column(header='fields', justify='right'),
        Column(header='golds', justify='right'),
        Column(header='batches', justify='right'),
        show_header=True)
    return table


def batches_table() -> Table:
    table = Table(
        Column(header='id', justify='right'),
        'batch',
        Column(header='size', justify='right'),
        Column(header='overlap', justify='right'),
        show_header=False)
    return table


def results_table() -> Table:
    table = Table(
        Column(header='label', justify='left'),
        Column(header='P', justify='right'),
        Column(header='R', justify='right'),
        Column(header='F1', justify='right'),
        show_header=True)
    return table


def print_dictionary(d: dict, header: str):
    """Print a dictionary, assumes integer keys and string values."""
    console.print(Panel(header))
    for n, name in sorted(d.items()):
        print(f' {n:2d}: {name}')
    print()


def print_panel_text_table(header: str, text: str, table: Table):
    console.print(Panel(header))
    lines =textwrap.wrap(
        text, width=80, initial_indent=' ', subsequent_indent=' ')
    for line in lines:
        console.print(line)
    console.print(table)


def parse_arguments():
    parser = argparse.ArgumentParser()
    d_help = "Open the ClamShack in DIR or create it if the directory does not exist"
    a_help = "Add the assets in FILE to the ClamShack in DIR"
    parser.add_argument('--dir', metavar='DIR', default='.', help=d_help)
    parser.add_argument('--assets', metavar='FILE', default=None, help=a_help)
    parser.add_argument('--debug', action='store_true')
    return parser.parse_args()


if __name__ == '__main__':

    args = parse_arguments()
    if args.debug:
        DEBUG = True
    Shell(ClamShack(args.dir, args.assets)).cmdloop()


messages = { 'bye': 'Bye bye sailor'}


COMMANDS = {

    'help': (
        'help\n help COMMAND',
        'Print list of available commands or print help for a command.'),

    'help_all': (
        'help_all',
        'Print all available commands with their help message.'),

    'history': (
        'history\n history reset',
        'Print the command history or reset it.'),
}


SHELL_COMMANDS = {

    'apps': (
        'apps\n apps (APP_INDEX | APP_NAME)',
        'List available CLAMS apps or select an app by index or name.'),

    'register': (
        'register URL',
        'Register an application with the Shack, the URL should include the scheme.'),

    'run': (
        'run NAME',
        'Run a job under a unique name, assumes you selected an app.'),

    'jobs': (
        'jobs\n jobs NAME',
        'Print list of jobs or information from one job.'),

    'source': (
        'source FILE',
        'Run the commands in the script file given'),

    'index': (
        'index',
        'Recreate the MMIF Storage index'),

    'params': (
        'params\n params reset\n params @FILE\n params PARAM=VALUE',
        'Print all parameters, reset all parameters, load parameters from a JSON file'
        ' or add/change a parameter.'),

    'show': (
        'show\n show error\n show errors',
        'Show current ClamShack settings, show the last error or show all errors.'),

    'describe': (
        'describe INT',
        'describe MMIF file at the given index'),

    'tree': (
        'tree [-p] [-f] [-v]',
        'Print the MMIF file tree from the current path. Include MMIF files'
        ' if the -f option is added and print the parameters (if relevant) if'
        ' the -p option is added, include both with the -v option.'),

    'pwd': (
        'pwd',
        'Print the current path in the MMIF storage.'),

    'dirs': (
        'dirs [-d] [-s]',
        'Print the directories at the current path. With the -d option three levels'
        ' in the directory strructure are printed. With the -s option perviously'
        ' saved directories are printed.'),

    'files': (
        'files',
        'Print the files at the current path.'),

    'cd': (
        "cd '~' | '..' | PATH | INDEX",
        'Change the current path in the MMIF storage, either by spelling out the'
        ' path or by giving an index from the dir command.'),

    'up': (
        'up\n up N',
        'Go up one directory in the MMIF storage or go up N levels.'),

    'home': (
        'home',
        'Go to the root directory in the MMIF storage.'),

    'goto': (
        'goto INT',
        'Go to a saved directory given the index.'),

    'prune': (
        'prune',
        'Prune the current directory and everything underneath. This cannot be undone.'),

    'view': (
        'view INT',
        'View a directory given the index.'),

    'quit': (
        'quit',
        'Exit the ClamShack.'),

    'search': (
        'search assets TERM'
        '\n search mmif TERM'
        '\n search app TERM'
        '\n search params (param=value)+',
        'Search for assets or mmif files matching a string, search for'
        ' directories where the pipeline includes and app name, or search'
        ' for directories with files creating where the app was given certain'
        ' parameters.'),

    'annotations': (
        'annotations'
        '\n annotations set DIRECTORY'
        '\n annotations select PROJECT_NAME',
        'Show all available annotation projects, load the annotation repository'
        ' in DIRECTORY, or select a project for further exploration.'),

}


ASHELL_COMMANDS = {

    'load': ('load DIRECTORY', 'Load the annotation repository from disk.'),

    'projects': (
        'projects'
        '\n projects INT|STR'
        '\n search params (param=value)+',
        'List all projects in the annotation repository or select a projects using'
        ' the project name or its index in the project dictionary.'),

    'batches': (
        'batches'
        '\n batches INT|STR'
        '\n search params (param=value)+',
        'List all batches in the annotation repository or select a batches using'
        ' the project name or its index in the project dictionary.'),

    'overlap': (
        'overlap',
        'Calculate the overlap of the sources in the shack with data drops in'
        ' the selected project')    
}


SHELL_COMMANDS.update(COMMANDS)
ASHELL_COMMANDS.update(COMMANDS)

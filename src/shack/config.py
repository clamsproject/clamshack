
messages = { 'bye': 'Bye bye sailor'}


# Names of tasks defined in the aapb-evaluations repository
TASKS = {
    'AutomaticSpeechRecognition', 
    'asr_eval', 
    'ForcedAlignment', 
    'KeyedInformationExtraction', 
    'NamedEntityGrounding', 
    'NamedEntityRecognition', 
    'TextRecognition', 
    'TimeFrameLabeling', 
    'TimePointLabeling'
}


COMMANDS = {

    # General command help for the command line interpreters

    'help': (
        'help\n help COMMAND',
        'Print list of available commands or print help for a command.'),

    'history': (
        'history\n history reset',
        'Print the command history or reset it.'),
}

SHELL_COMMANDS = {

    # Command help for commands specifically for the Shell CLI

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
        'Exit the ClamShell.'),

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


ESHELL_COMMANDS = {

    # Command help for commands specifically for the EvaluationShell CLI

    'load': (
        'load DIRECTORY',
        'Load the annotation or evaluation repository from disk.'),

    'show': (
        'show\n show error|errors\n show batch (INT|STR)?\n show task (INT|STR)',
        'Show current Evaluation settings or show the last or all errors. '
        'With the batch option, show the selected batch with its comment or do that '
        'for the batch identified by name or by the index in the batches list. With '
        'the task option, show the selected task with its comment or do that for the '
        'task identified by name or by the index in the tasks list.'),

    'projects': (
        'projects'
        '\n projects INT|STR',
        'List all projects in the annotation repository or select a projects using'
        ' the project name or its index in the project dictionary.'),

    'batches': (
        'batches'
        '\n batches INT|STR',
        'List all batches in the annotation repository or select a batch using'
        ' the batch name or its index in the batch dictionary.'),

    'tasks': (
        'tasks'
        '\n tasks INT|STR',
        'List all tasks in the evaluation repository or select a task using'
        ' the task name or its index in the task dictionary.'),

    'quit': (
        'quit',
        'Exit the EvaluationShell and return the current settings from that shell.')
}


SHELL_COMMANDS.update(COMMANDS)
ESHELL_COMMANDS.update(COMMANDS)



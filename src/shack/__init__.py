
# This is a temporary hack which will be replaced with a proper import in the requirements file
# once the code has been pulled apart and we have a proper installable module.
import sys
sys.path.append('/Users/marc/Documents/git/clams/aapb/aapb-brandeis-datahousing')

from shack.main import ClamShack, ShackError
from shack.main import History, Assets, StoragePath, MmifIndex, Job

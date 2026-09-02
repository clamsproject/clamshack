
# This is a temporary hack which will be replaced with a proper import in the requirements
# file once the code has been pulled apart and we have a proper installable module for the
# datahousing code.
import sys
import os
from dotenv import load_dotenv
load_dotenv()
sys.path.append(os.environ['DATAHOUSING_CODE'])

from shack.main import ClamShack, ShackError
from shack.main import History, Assets, StoragePath, MmifIndex, Job

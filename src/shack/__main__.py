import sys
from shack import batch


if sys.argv[1] == 'batch':
	sys.argv.pop(1)
	args = batch.arg_parser().parse_args()
	batch.main(args)

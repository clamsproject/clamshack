import sys
from shack import batch, annotations


if sys.argv[1] == 'batch':
    sys.argv.pop(1)
    args = batch.arg_parser().parse_args()
    batch.main(args)


if sys.argv[1] == 'anno':

    # experimenting with the repository code
    
    repo = annotations.Repository(sys.argv[2])
    print(f'\n{repo}')

    root_tree = repo.repo.heads['main'].commit.tree
    batches_tree = repo.root / 'batches'
    batches = [b for b in batches_tree]

    #print()
    #print(repo.repo.heads)
    #print(repo.repo.branches)
    #print(repo.branches)

    print()
    for n in range(3):
        print(repo.batches[n])

    print()
    for n in range(len(repo.projects)):
        print(f'{repo.projects[n]}')

    neproj = repo.get_project('newshour-namedentity')
    print(f'\n{neproj}')
    first_gold = neproj.golds[0]
    print('BLOB', first_gold, first_gold.name)
    print(first_gold.content[:200])
    drop = neproj._drops['220601-aapb-collaboration-21']
    print(drop)
    print(drop.file_names[0])
    print(drop.file_content(drop.file_names[0])[:200])

    swtproj = repo.get_project('scene-recognition')
    drop = swtproj._drops['240814-aapb-collaboration-27-e']
    identifier = 'cpb-aacip-00a9ed7f2ba'
    print(drop)
    #print(drop.file_names)
    print(identifier in drop.file_names)


'''
from shack.annotations import Repository
repo = Repository('../aapb/aapb-annotations')
identifier = 'cpb-aacip-00a9ed7f2ba'
swtproj = repo.get_project('scene-recognition')
drop = swtproj._drops['240814-aapb-collaboration-27-e']
print(drop)
print(drop.file_names)
'''

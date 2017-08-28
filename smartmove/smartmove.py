#!/usr/bin/env python

import sys
import os
import shutil
from kcl.fileops import file_exists
from kcl.dirops import dir_exists
from kcl.printops import eprint


def compare_files(source, dest, recommend_larger=True):
    assert file_exists(source)
    assert file_exists(dest)
    source_stat = os.stat(source)
    dest_stat = os.stat(dest)
    eprint("source:", source)
    eprint("dest  :", dest)
    #eprint("source_stat:", source_stat)
    #eprint("dest_stat:", dest_stat)
    if source_stat.st_size == dest_stat.st_size:
        eprint("files are the same size")
        return dest
    #elif source_stat.st_size > dest_stat.st_size:
    #    eprint("the source file is larger:")
    #else source_stat.st_size < dest_stat.st_size:
    else:
        eprint("files differ in size:")
        eprint("  source:", source_stat.st_size)
        eprint("  dest  :", dest_stat.st_size)
        if recommend_larger:
            return source if source_stat.st_size > dest_stat.st_size else dest
        else:
            return dest if source_stat.st_size > dest_stat.st_size else source



def smartmove(source, dest):
    assert file_exists(source)
    if file_exists(dest):
        assert not dest.endswith('/')
        file_to_keep = compare_files(source=source, dest=dest)
        eprint("file_to_keep:", file_to_keep)
        return False
    elif dir_exists(dest):
        if dest.endswith('/'):
            dest = dest[:-1]
        source_filename = os.path.basename(source)
        dest = dest + '/' + source_filename
        assert not dir_exists(dest)
        if file_exists(dest):
            file_to_keep = compare_files(source=source, dest=dest, recommend_larger=True)
            eprint("file_to_keep:", file_to_keep)
            if file_to_keep == dest:
                eprint("keeping dest file, no need to mv, just rm source")
                os.remove(source)
                return True
            elif file_to_keep == source:
                eprint("moving source to dest, need to rm dest first")
                os.remove(dest)
                shutil.move(source, dest)
                return True
        else:
            shutil.move(source, dest)
            return True


if __name__ == '__main__':
    source = sys.argv[1]
    assert file_exists(source)
    dest = sys.argv[2]
    result = smartmove(source=source, dest=dest)
    print('result:', result, '\n')
    if not result:
        eprint("-------------FALSE-------------- sleeping.")
        while(1):
            sleep(1)
            pass

#!/usr/bin/env python

import sys
import os
import shutil
import click
from kcl.fileops import file_exists
from kcl.dirops import dir_exists
from kcl.printops import eprint


def compare_files(source, destination, recommend_larger=True):
    assert file_exists(source)
    assert file_exists(destination)
    source_stat = os.stat(source)
    destination_stat = os.stat(destination)
    eprint("source:", source)
    eprint("destination  :", destination)
    #eprint("source_stat:", source_stat)
    #eprint("destination_stat:", destination_stat)
    if source_stat.st_size == destination_stat.st_size:
        eprint("files are the same size")
        return destination
    #elif source_stat.st_size > destination_stat.st_size:
    #    eprint("the source file is larger:")
    #else source_stat.st_size < destination_stat.st_size:
    else:
        eprint("files differ in size:")
        eprint("  source:", source_stat.st_size)
        eprint("  destination  :", destination_stat.st_size)
        if recommend_larger:
            return source if source_stat.st_size > destination_stat.st_size else destination
        else:
            return destination if source_stat.st_size > destination_stat.st_size else source


def smartmove_file(source, destination, verbose=False):
    assert file_exists(source)
    if file_exists(destination):
        assert not destination.endswith('/')
        file_to_keep = compare_files(source=source, destination=destination)
        eprint("file_to_keep:", file_to_keep)
        return False
    elif dir_exists(destination):
        if destination.endswith('/'):
            destination = destination[:-1]
        source_filename = os.path.basename(source)
        destination = destination + '/' + source_filename # hmmm use a new var?
        assert not dir_exists(destination)
        if file_exists(destination):
            file_to_keep = compare_files(source=source, destination=destination, recommend_larger=True)
            eprint("file_to_keep:", file_to_keep)
            if file_to_keep == destination:
                eprint("keeping destination file, no need to mv, just rm source")
                os.remove(source)
                return True
            elif file_to_keep == source:
                eprint("moving source to destination, need to rm destination first")
                os.remove(destination)
                shutil.move(source, destination)
                return True
        else:
            if verbose:
                eprint(source, "->", destination)
            shutil.move(source, destination)
            return True
    else:
        eprint("destination:", destination, "is not a file or directory, exiting.")
        return False


@click.command()
@click.argument('sources', nargs=-1)
@click.argument('destination', nargs=1)
@click.option('--verbose', required=False, is_flag=True)
def smartmove(sources, destination, verbose):
    for source in sources:
        assert file_exists(source)
        smartmove_file(source, destination, verbose)



#!/usr/bin/env python

import os
import shutil
import click
from kcl.fileops import file_exists
from kcl.dirops import dir_exists
from kcl.printops import eprint

JUNK = '/home/user/_youtube/sources_delme/youtube/'

def compare_files(source, destination, recommend_larger=True, skip_percent=False):
    eprint("source     :", source)
    eprint("destination:", destination)
    assert file_exists(source)
    assert file_exists(destination)
    source_stat = os.stat(source)
    destination_stat = os.stat(destination)
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

        if skip_percent:
            assert skip_percent < 100
            assert skip_percent > 0

            percent_difference = \
                abs((source_stat.st_size-destination_stat.st_size) / max(source_stat.st_size, destination_stat.st_size))
            if percent_difference < skip_percent:
                eprint("returning destination because percent_difference: ", percent_difference, "is < skip_percent: ", skip_percent)
                return destination

        if recommend_larger:
            return source if source_stat.st_size > destination_stat.st_size else destination
        else:
            return destination if source_stat.st_size > destination_stat.st_size else source

def smartmove_file(source, destination, makedirs, verbose=False, skip_percent=False):
    #eprint("\n")
    eprint("source     :", source)
    eprint("destination:", destination)
    assert file_exists(source)
    if file_exists(destination):
        assert not destination.endswith('/')
        file_to_keep = compare_files(source=source, destination=destination, recommend_larger=True, skip_percent=skip_percent)
        eprint("file_to_keep:", file_to_keep)
        if file_to_keep == destination:
            eprint("the destination file is being kept, so need to delete the source since it's not being moved")
            shutil.move(source, JUNK)
        elif file_to_keep == source:
            eprint("the source:", source, "is being kept, so need to move it to overwrite the destination")
            shutil.move(source, destination)
        else:
            eprint("file_to_keep:", file_to_keep, "does not match the source or destination, that's a bug")
            exit(1)

        return False
    elif dir_exists(destination):
        if destination.endswith('/'): # should be fixed with a decorator
            destination = destination[:-1]
        source_filename = os.path.basename(source)
        destination = destination + '/' + source_filename # hmmm use a new var?
        assert not dir_exists(destination)
        if file_exists(destination):
            file_to_keep = compare_files(source=source, destination=destination, recommend_larger=True, skip_percent=skip_percent)
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
        destination_folder = os.path.dirname(destination)
        if makedirs:
            os.makedirs(destination_folder, exist_ok=True)
            if verbose:
                eprint(source, "->", destination)
            shutil.move(source, destination)
        else:
            eprint("destination:", destination, "is not a file or directory, exiting.")
            raise FileNotFoundError


@click.command()
@click.argument('sources', nargs=-1)
@click.argument('destination', nargs=1)
@click.option('--verbose', required=False, is_flag=True)
@click.option('--makedirs', required=False, is_flag=True)
def smartmove(sources, destination, verbose, makedirs):
    for source in sources:
        assert file_exists(source)
        smartmove_file(source=source, destination=destination, verbose=verbose, makedirs=makedirs)



#!/usr/bin/env python

import os
import shutil
from subprocess import CalledProcessError
import click
from kcl.fileops import path_is_file
from kcl.fileops import empty_file
from kcl.dirops import path_is_dir
from kcl.commandops import run_command
from kcl.printops import eprint
from classify.classify import classify
from icecream import ic
from shutil import get_terminal_size
ic.lineWrapWidth, _ = get_terminal_size((80, 20))

JUNK = '/home/user/_youtube/sources_delme/youtube/'


def ffmpeg_file_is_corrupt(file, write_verification=False):
    command = "/home/cfg/media/ffmpeg/exit_on_first_error_found"
    command += " "
    command += '"' + os.fsdecode(file) + '"'
    try:
        run_command(command, verbose=True)
        if write_verification:
            eprint("could write verification file now, need hash")
    except CalledProcessError:
        return True
    return False


def compare_files_by_size(source, destination, recommend_larger=True, skip_percent=False):
    #ic(source)
    #ic(destination)
    assert path_is_file(source)
    assert path_is_file(destination)
    source_stat = os.stat(source)
    destination_stat = os.stat(destination)
    #eprint("source_stat:", source_stat)
    #eprint("destination_stat:", destination_stat)
    if source_stat.st_size == destination_stat.st_size:
        eprint("files are the same size")
        return destination

    eprint("files differ in size:")
    eprint("  source     :", source_stat.st_size)
    eprint("  destination:", destination_stat.st_size)

    if skip_percent:
        assert skip_percent < 100
        assert skip_percent > 0

        percent_difference = \
            abs((source_stat.st_size - destination_stat.st_size) / max(source_stat.st_size, destination_stat.st_size))
        if percent_difference < skip_percent:
            eprint("returning destination because percent_difference: ", percent_difference, "is < skip_percent: ", skip_percent)
            assert False
            return destination

    if recommend_larger:
        return source if source_stat.st_size > destination_stat.st_size else destination
    else:
        return destination if source_stat.st_size > destination_stat.st_size else source


def smartmove_file(source, destination, makedirs, verbose=False, skip_percent=False):
    #eprint("\n")
    eprint("source     :", source)
    eprint("destination:", destination)
    assert path_is_file(source)
    if path_is_file(destination):
        assert not destination.endswith('/')
        source_classification = classify(source)

        if source_classification == 'media':
            source_corrupt = ffmpeg_file_is_corrupt(source)
            destination_corrupt = ffmpeg_file_is_corrupt(destination)
            if source_corrupt and destination_corrupt:
                eprint("source and destination are corrupt according to ffmpeg, relying on file size instead")
                file_to_keep = compare_files_by_size(source=source, destination=destination, recommend_larger=True, skip_percent=skip_percent)
                eprint("file_to_keep:", file_to_keep)
            elif source_corrupt:
                file_to_keep = destination
                eprint("source is corrupt, keeping destination")  # bug what if destination is much smaller?
            elif destination_corrupt:
                file_to_keep = source
                eprint("destination is corrupt, keeping source")  # bug what if source is much smaller?
            else:   # neither are corrupt...
                file_to_keep = compare_files_by_size(source=source, destination=destination, recommend_larger=True, skip_percent=skip_percent)
                eprint("did size comparison, file_to_keep:", file_to_keep)
        else:
            file_to_keep = compare_files_by_size(source=source, destination=destination, recommend_larger=True, skip_percent=skip_percent)
            eprint("(non media) did size comparison, file_to_keep:", file_to_keep)


        if empty_file(file_to_keep):
            assert empty_file(source)
            assert empty_file(destination)

        if file_to_keep == destination:
            eprint("the destination file is being kept, so need to delete the source since it's not being moved")
            try:
                shutil.move(source, JUNK)  # https://bugs.python.org/issue26791
            except OSError:
                os.unlink(source)
                eprint("unlinked:", source)
            #except IsADirectoryError:
            #    os.unlink(source)

        elif file_to_keep == source:
            eprint("the source:", source, "is being kept, so need to move it to overwrite the destination")
            shutil.move(source, destination)
        else:
            eprint("file_to_keep:", file_to_keep, "does not match the source or destination, that's a bug")
            exit(1)

        return False

    elif path_is_dir(destination):
        if destination.endswith('/'): # should be fixed with a decorator
            destination = destination[:-1]
        source_filename = os.path.basename(source)
        destination = destination + '/' + source_filename # hmmm use a new var?
        assert not path_is_dir(destination)
        if path_is_file(destination):
            file_to_keep = compare_files_by_size(source=source, destination=destination, recommend_larger=True, skip_percent=skip_percent)
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
        ic(source)
        assert path_is_file(source)
        smartmove_file(source=source, destination=destination, verbose=verbose, makedirs=makedirs)


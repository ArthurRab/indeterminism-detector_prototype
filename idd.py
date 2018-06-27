from filecmp import dircmp
import os


def getPath(path):
    # Adds a '/' to the end of the given string if that string is a path to a directory
    # as opposed to a file
    if os.is_dir(path, follow_symlinks=False):
        path += "/"

    return path


def compdirs(left, right, diff=None, path=""):
    if diff == None:
        diff = dircmp(left, right)

    only_in_left = [path + i + "/" for i in diff.only_in_left]
    only_in_right = [path + i + "/" for i in diff.only_in_right]
    diff_files = [path + i + "/" for i in diff.diff_files]

    # Checks for symbolic links (dircmp classifies ones that point to
    # non-existant files as funny)

    for funny_file in diff.funny_files:
        if not(os.path.islink(left+"/"+path+funny_file) and os.path.islink(right+"/"+path+funny_file) and
                os.readlink(left+"/"+path+funny_file) == os.readlink(right+"/"+path+funny_file)):
            diff_files.append(path+funny_file)

    for diff_dir in diff.subdirs:
        oil, oir, df = compdirs(left, right,
                                diff.subdirs[diff_dir], path+diff_dir+"/")

        only_in_left += oil
        only_in_right += oir
        diff_files += df

    return only_in_left, only_in_right, diff_files


compdirs("testing_data/1", "testing_data/2")

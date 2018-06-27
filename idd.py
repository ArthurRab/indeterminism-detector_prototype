from filecmp import dircmp
import os
import tarfile
from json import JSONDecoder


def getPath(path, prepath=""):
    # Adds a '/' to the end of the given string if that string is a path to a directory
    # as opposed to a file
    if os.path.isdir(prepath+"/"+path):
        path += "/"

    return path


def compdirs(left, right, diff=None, path=""):
    if diff == None:
        diff = dircmp(left, right)

    left_only = [getPath(path + i, left) for i in diff.left_only]
    right_only = [getPath(path + i, left) for i in diff.right_only]
    diff_files = [path + i for i in diff.diff_files]

    # Checks for symbolic links (dircmp classifies ones that point to
    # non-existant files as funny)
    for funny_file in diff.funny_files:
        if not(os.path.islink(left+"/"+path+funny_file) and os.path.islink(right+"/"+path+funny_file) and
                os.readlink(left+"/"+path+funny_file) == os.readlink(right+"/"+path+funny_file)):
            diff_files.append(path+funny_file)

    for diff_dir in diff.subdirs:
        oil, oir, df = compdirs(left, right,
                                diff.subdirs[diff_dir], path+diff_dir+"/")

        left_only += oil
        right_only += oir
        diff_files += df

    return left_only, right_only, diff_files


def findDifferences(tar1_path, tar2_path):
    tar_pair = (tar1_path, tar2_path)
    manifests = []

    decoder = JSONDecoder()
    for i in range(1, 3):
        tar_path = tar_pair[i-1]

        folder = "tar{}_contents".format(str(i))
        if(os.path.isdir(folder)):
            os.rmdir(folder)
        os.mkdir(folder)

        tar = tarfile.open(tar_path, mode='r')

        manifest = decoder.decode(tar.extractfile(
            "manifest.json").read().decode("utf-8"))[0]
        manifests.append(manifest)

        print(manifest["Layers"])


findDifferences("testing_data/1.tar", "testing_data/2.tar")

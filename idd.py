from filecmp import dircmp
import os
import tarfile
from json import JSONDecoder
import shutil
import sys
import argparse


class ImageTar():
    id_counter = 1

    def __init__(self, tar_path, contents_path=""):
        self.tar_id = ImageTar.id_counter
        ImageTar.id_counter += 1

        folder = contents_path+"tar{}_contents".format(str(self.tar_id))

        if(os.path.isdir(folder)):
            shutil.rmtree(folder)
        os.mkdir(folder)

        self.contents_folder = os.path.abspath(folder) + "/"

        self.tar = tarfile.open(tar_path, mode='r')

        decoder = JSONDecoder()
        manifest = decoder.decode(self.tar.extractfile(
            "manifest.json").read().decode("utf-8"))[0]
        self.image_id = manifest["Config"].split(".")[0]
        self.layers = manifest["Layers"]

    def get_diff_layers(self, other_tar):
        diff_layers = []
        for i in range(min(len(self.layers), len(other_tar.layers))):
            if self.layers[i] != other_tar.layers[i]:
                diff_layers.append(i)
        return diff_layers

    def get_path_to_layer_contents(self, layer_num):
        path = self.contents_folder+"layer_"+str(layer_num) + "/"
        if not os.path.isdir(path):
            os.mkdir(path)
            self.tar.extract(self.layers[layer_num], path=self.contents_folder)
            layer_tar = tarfile.open(
                self.contents_folder + self.layers[layer_num])
            try:
                layer_tar.extractall(path)
            except:
                print("Some files were unable to be extracted from image: {} layer: {}. Are your base layers different?".format(
                    self.tar_id, layer_num), file=sys.stderr)
        return path

    def cleanup(self):
        shutil.rmtree(self.contents_folder)


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


def findDifferences(tar1_path, tar2_path, max_depth=float("inf"), max_differences=float("inf"), print_differences=False, cancel_cleanup=False):
    tar1 = ImageTar(tar1_path)
    tar2 = ImageTar(tar2_path)

    diff_layers = tar1.get_diff_layers(tar2)

    diff_count = 0

    for layer in diff_layers:
        if layer >= max_depth:
            break

        files = compdirs(tar1.get_path_to_layer_contents(layer),
                         tar2.get_path_to_layer_contents(layer))

        print()
        if files != ([], [], []):
            print("Layer {}:\n".format(layer))
            diff_count += 1

        text = ("Only in image 1:\n", "Only in image 2:\n",
                "Differing common files:\n")
        for i in range(3):
            if len(files[i]) != 0:
                print(text[i])
            for file in files[i]:
                print(file)

        if diff_count >= max_differences:
            break

    print()
    if len(tar1.layers) != len(tar2.layers):
        print("NOTE: Images have different number of layers\n")

    if not cancel_cleanup:
        tar1.cleanup()
        tar2.cleanup()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("tar1", help="First image tar path", type=str)
    parser.add_argument("tar2", help="Second image tar path", type=str)
    parser.add_argument("-c", "--cancel_cleanup",
                        help="Leaves all the extracted files after program finishes running", action="store_true")
    parser.add_argument("-l", "--max_layer",
                        help="Only compares until given layer (exclusive, starting at 0)", type=int, default=float("inf"))
    parser.add_argument("-d", "--max_differences",
                        help="Stops after MAX_DIFFERENCES different layers are found", type=int, default=float("inf"))
    parser.add_argument("-v", "--verbose",
                        help="Print differences between files (as well as their names) NOT IMPLEMENTED", action="store_true")

    args = parser.parse_args()

    findDifferences(args.tar1, args.tar2, cancel_cleanup=args.cancel_cleanup,
                    max_differences=args.max_differences, max_depth=args.max_layer, print_differences=args.verbose)

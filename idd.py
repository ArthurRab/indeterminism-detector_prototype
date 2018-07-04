from filecmp import dircmp
import os
import tarfile
from json import JSONDecoder
import shutil
import sys
import argparse
import difflib


class ImageTar():
    id_counter = 1

    def __init__(self, tar_path, contents_path=""):
        self.tar_id = ImageTar.id_counter
        ImageTar.id_counter += 1

        # Create a folder where the contents of layers in this image will be extracted
        folder = contents_path+"tar{}_contents".format(str(self.tar_id))

        if(os.path.isdir(folder)):
            shutil.rmtree(folder)
        os.mkdir(folder)

        self.contents_folder = os.path.abspath(folder) + "/"

        self.tar = tarfile.open(tar_path, mode='r')

        # Extract the list of layer paths from the manigest.json file.
        decoder = JSONDecoder()
        manifest = decoder.decode(self.tar.extractfile(
            "manifest.json").read().decode("utf-8"))[0]
        self.layers = manifest["Layers"]

    def get_diff_layers(self, other_tar):
        # Returns a list of indicies of layers which differ between self and other_tar
        diff_layers = []
        for i in range(min(len(self.layers), len(other_tar.layers))):
            if self.layers[i] != other_tar.layers[i]:
                diff_layers.append(i)
        return diff_layers

    def get_path_to_layer_contents(self, layer_num):
        # Returns the path to the root of the folder where the contents of the
        # given layer are kept. If it has not yet been extracted, it also extracts it.
        path = self.contents_folder+"layer_"+str(layer_num) + "/"
        if not os.path.isdir(path):
            os.mkdir(path)
            self.tar.extract(self.layers[layer_num], path=self.contents_folder)
            layer_tar = tarfile.open(
                self.contents_folder + self.layers[layer_num])
            for member in layer_tar:
                try:
                    layer_tar.extract(member, path)
                except:
                    print("Some files were unable to be extracted from image: {} layer: {}. Are your base layers different?".format(
                        self.tar_id, layer_num), file=sys.stderr)
        return path

    def cleanup(self):
        # Removes all the artifacts this object produced
        shutil.rmtree(self.contents_folder)


def getPath(path, prepath=""):
    # Adds a '/' to the end of the given string if that string is a path to a
    # directory as opposed to a file
    if os.path.isdir(prepath+"/"+path):
        path += "/"

    return path


def compdirs(left, right, diff=None, path=""):
    # Compares all files and directories that differ among the two given
    # directories. Returns a 3-tuple of the form (left_only, right_only, diff_files)
    # where left_only and right_only are lists of files unique to the corresponding
    # directory, and diff_files is a list of common files which are not identical.
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

    # Recursive call on subdirectories
    for diff_dir in diff.subdirs:
        oil, oir, df = compdirs(left, right,
                                diff.subdirs[diff_dir], path+diff_dir+"/")

        left_only += oil
        right_only += oir
        diff_files += df

    return left_only, right_only, diff_files


def findDifferences(tar1_path, tar2_path, max_depth=float("inf"), max_differences=float("inf"), print_differences=False, cancel_cleanup=False):
    # Main part of the program
    # Uses all of the other functions to print out, in a human-readable form,
    # the differences between the two given image tarballs
    tar1 = ImageTar(tar1_path)
    tar2 = ImageTar(tar2_path)

    diff_layers = tar1.get_diff_layers(tar2)

    diff_count = 0

    for layer in diff_layers:
        # Stop if reaches max depth or max number of differences (optional params)
        if layer >= max_depth:
            break
        if diff_count >= max_differences:
            break

        # Get the 3-tuple of lists of files that differ between the layers
        files = compdirs(tar1.get_path_to_layer_contents(layer),
                         tar2.get_path_to_layer_contents(layer))

        print("\nLayer {}:\n".format(layer))
        diff_count += 1

        # If the layer has no differences to report
        if files == ([], [], []):
            print("No differences found, but layer ids are different.")

        differing_common_files = files[2]

        if len(differing_common_files) > 0:
            print("Differing common files:\n")
        for f in differing_common_files:
            if not print_differences:
                # print the file name if verbosity was not requested
                print(f)
            else:
                # print the file name and try to see the differences between the files
                print(f+":")
                try:
                    file1 = open(tar1.get_path_to_layer_contents(layer)+f)
                    file2 = open(tar2.get_path_to_layer_contents(layer)+f)

                    for line in difflib.unified_diff(list(file1), list(file2)):
                        print(line)
                    print("EOF\n")
                except:
                    # unable to compare the files, probably because at
                    # least one of them is binary. Skip it.
                    print("Skipping binary file.\n")

        text = ("Only in image 1:\n", "Only in image 2:\n")

        for i in range(2):
            if len(files[i]) > 0:
                print(text[i])
            for f in files[i]:
                print(f)

    print()
    if len(tar1.layers) != len(tar2.layers):
        print("NOTE: Images have different number of layers\n")

    if not cancel_cleanup:
        # Delete all artifacts unless asked not to
        tar1.cleanup()
        tar2.cleanup()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("tar1", help="First image tar path", type=str)
    parser.add_argument("tar2", help="Second image tar path", type=str)
    parser.add_argument("-c", "--cancel_cleanup",
                        help="leaves all the extracted files after program finishes running", action="store_true")
    parser.add_argument("-l", "--max_layer",
                        help="only compares until given layer (exclusive, starting at 0)", type=int, default=float("inf"))
    parser.add_argument("-d", "--max_differences",
                        help="stops after MAX_DIFFERENCES different layers are found", type=int, default=float("inf"))
    parser.add_argument("-v", "--verbose",
                        help="print differences between files (as well as their names)", action="store_true")

    args = parser.parse_args()

    findDifferences(args.tar1, args.tar2, cancel_cleanup=args.cancel_cleanup,
                    max_differences=args.max_differences, max_depth=args.max_layer, print_differences=args.verbose)

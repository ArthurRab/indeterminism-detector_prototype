from __future__ import print_function
from filecmp import dircmp, cmp
import os
import tarfile
from json import JSONDecoder
import shutil
import sys
import argparse
import difflib
import atexit
"""Relevant parts of the structure of a valid image tarball (tarball.tar):

  tarball.tar/
    manifest.json
    <layer1_id>/
      layer.tar
    <layer2_id>/
      layer.tar
    ...

The manifest.json should have a field named 'layers' which has the paths to
the layer.tar's in the same order as the layers were installed:
Ex. "layers" : ["<layer1_id>/layer.tar", "<layer2_id>/layer.tar"]
"""


class ImageTar():
  """Fields:

            Instance:
              tar_id: int - This objects id, used to determine where it stores
              its
              extracted contents
              contents_folder: str - The path to the folder where we store
              temporary
              extracted files
              tar: file - The image's tarball as a file open for reading
              layers: list of str - Chronological list of the path to each
              layer's
              tarball within the original tar

            Static:
              id_counter: int - Counter to keep track of each ImageTar's object
              id
              (for
              giving it a contents folder)
          """
  id_counter = 1

  def __init__(self, tar_path, contents_path=""):
    """Parameters:

                      tar_path: str, relative or absolute path to the given
                      tarball
                      contents_path: str, path where the tar's content folder
                      will
                      be
                      created
                                    by default, it is in the current directory
                    """

    self.tar_id = ImageTar.id_counter
    ImageTar.id_counter += 1

    # Create a folder where the contents of layers in this image will be extracted
    # If the script is called normally, would produce tar1_contents and
    # tar2_contents folders in the working directory
    # All files created by this object will be placed in here
    folder = os.path.join(contents_path, "tar{}_contents".format(
        str(self.tar_id)))

    if (os.path.isdir(folder)):
      shutil.rmtree(folder)
    os.mkdir(folder)

    self.contents_folder = os.path.abspath(folder)

    self.tar = tarfile.open(tar_path, mode="r")

    # Extract the list of layer paths from the manigest.json file.
    decoder = JSONDecoder()
    try:
      manifest = decoder.decode(
          self.tar.extractfile("manifest.json").read().decode("utf-8"))[0]
      self.layers = manifest["Layers"]
    except Exception as e:
      print(
          e,
          "Unable to extract manifest.json from image {}. \
              Make sure it is a valid image tarball".format(self.tar_id),
          file=sys.stderr)

  def get_diff_layer_indicies(self, other_tar):
    # Returns a list of indicies of layers which differ between self and other_tar
    diff_layers = []
    for i in range(min(len(self.layers), len(other_tar.layers))):
      if self.layers[i] != other_tar.layers[i]:
        diff_layers.append(i)
    return diff_layers

  def get_path_to_layer_contents(self, layer_num):
    # Returns the path to the root of the folder where the contents of the
    # given layer are kept. If it has not yet been extracted, it also extracts it.
    # Example path: tar1_contents/layer2 where the numbers can vary
    path = os.path.join(self.contents_folder, "layer_" + str(layer_num))
    if not os.path.isdir(path):
      os.mkdir(path)
      self.tar.extract(self.layers[layer_num], path=self.contents_folder)
      layer_tar = tarfile.open(
          os.path.join(self.contents_folder, self.layers[layer_num]))
      try:
        layer_tar.extractall(path)
      except:
        print(
            "Some files were unable to be extracted from image: {} layer: {}. Are your base layers different?".
            format(self.tar_id, layer_num),
            file=sys.stderr)
    return path

  def cleanup(self):
    # Removes all the artifacts this object produced
    shutil.rmtree(self.contents_folder)


def compdirs(left, right, diff=None, path=""):
  # Compares all files and directories that differ among the two given
  # directories. Returns a 3-tuple of the form (left_only, right_only, diff_files)
  # where left_only and right_only are lists of files unique to the corresponding
  # directory, and diff_files is a list of common files which are not identical.
  if diff == None:
    diff = dircmp(left, right)

  left_only = [os.path.join(path, i, left) for i in diff.left_only]
  right_only = [os.path.join(path, i, right) for i in diff.right_only]
  diff_files = [os.path.join(path, i) for i in diff.diff_files]

  # This sometimes mislabels different files as same (since it uses cmp with shall=True),
  # so we double check with shallow=False

  for f in diff.same_files:
    try:
      if not cmp(
          os.path.join(left, path, f),
          os.path.join(right, path, f),
          shallow=False):
        diff_files.append(os.path.join(path, f))
    except Exception as e:
      print("Error while comparing the two version of " + os.path.join(path, f),
            e)

  # Checks for symbolic links (dircmp classifies ones that point to
  # non-existant files as funny)
  for funny_file in diff.funny_files:
    if not (os.path.islink(os.path.join(left, path, funny_file)) and
            os.path.islink(os.path.join(right, path, funny_file)) and
            os.readlink(os.path.join(left, path, funny_file)) == os.readlink(
                os.path.join(right, path, funny_file))):
      diff_files.append(os.path.join(path, funny_file))

  # Recursive call on subdirectories (dicrmp does not automatically compare
  # subdirectories, diff.diff_files only has files from the base directory)
  for diff_dir in diff.subdirs:
    oil, oir, df = compdirs(left, right, diff.subdirs[diff_dir],
                            os.path.join(path, diff_dir))

    left_only += oil
    right_only += oir
    diff_files += df

  return left_only, right_only, diff_files


def findDifferences(tar1_path,
                    tar2_path,
                    max_depth=float("inf"),
                    stop_at_first_difference=False,
                    print_differences=False,
                    cancel_cleanup=False,
                    force=False):
  # Main part of the program
  # Uses all of the other functions to print out, in a human-readable form,
  # the differences between the two given image tarballs

  tar1 = ImageTar(tar1_path)
  tar2 = ImageTar(tar2_path)

  if not cancel_cleanup:
    # Delete all artifacts unless asked not to (upon program exiting)
    def cleanup():
      tar1.cleanup()
      tar2.cleanup()

    atexit.register(cleanup)

  if len(tar1.layers) != len(tar2.layers):
    print("Images have different number of layers")
    if not force:
      print("Use -f | --force flag to proceed\n")
      exit(1)
  print()

  diff_layers = tar1.get_diff_layer_indicies(tar2)

  for layer in diff_layers:
    # Stop if reaches max depth or max number of differences (optional params)
    if layer >= max_depth:
      break

    # Get the 3-tuple of lists of files that differ between the layers
    files = compdirs(
        tar1.get_path_to_layer_contents(layer),
        tar2.get_path_to_layer_contents(layer))

    print("\nLayer {}:\n".format(layer))

    # If the layer has no differences to report
    if files == ([], [], []):
      print("No differences found, but layer ids are different.")

    diff_files = files[2]

    if len(diff_files) > 0:
      print("Differing common files:\n")
    for f in diff_files:
      if not print_differences:
        # print the file name if verbosity was not requested
        print(f)
      else:
        # print the file name and try to see the differences between the files
        print(f + ":")
        try:
          file1 = open(os.path.join(tar1.get_path_to_layer_contents(layer), f))
          file2 = open(os.path.join(tar2.get_path_to_layer_contents(layer), f))

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

    # Stop here if the user requested so
    if stop_at_first_difference:
      break

  print()


if __name__ == "__main__":
  """Examples of usage:

  Basic:
    python idd.py path/to/image1.tar path/to/image2.tar

  Including file content differences:
    python -v idd.py path/to/image1.tar path/to/image2.tar

  Only compare first 4 layers, and stop after a difference was found
    python -d -l 4 idd.py path/to/image1.tar path/to/image2.tar

  """
  parser = argparse.ArgumentParser()

  parser.add_argument("tar1", help="First image tar path", type=str)
  parser.add_argument("tar2", help="Second image tar path", type=str)
  parser.add_argument(
      "-c",
      "--cancel_cleanup",
      help="leaves all the extracted files after program finishes running",
      action="store_true")
  parser.add_argument(
      "-d",
      "--first_diff",
      help="stops after a pair of layers which differ are found",
      action="store_true")
  parser.add_argument(
      "-f",
      "--force",
      help="run even if the images don't have the same number of layers",
      action="store_true")
  parser.add_argument(
      "-l",
      "--max_layer",
      help="only compares until given layer (exclusive, starting at 0)",
      type=int,
      default=float("inf"))
  parser.add_argument(
      "-v",
      "--verbose",
      help="print differences between files (as well as their names)",
      action="store_true")

  args = parser.parse_args()

  findDifferences(
      tar1_path=args.tar1,
      tar2_path=args.tar2,
      cancel_cleanup=args.cancel_cleanup,
      stop_at_first_difference=args.first_diff,
      max_depth=args.max_layer,
      print_differences=args.verbose,
      force=args.force)

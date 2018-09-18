# indeterminism-detector_prototype

This was one of my intern projects at Google in summer 2018.

Now available at: https://github.com/bazelbuild/rules_docker/blob/master/contrib/idd.py



Tool to detect which files cause indeterminism in the building of docker images.

<pre>
positional arguments:
  tar1                  First image tar path
  tar2                  Second image tar path

optional arguments:
  -h, --help            show this help message and exit
  -c, --cancel_cleanup  leaves all the extracted files after program finishes
                        running
  -d MAX_DIFFERENCES, --max_differences MAX_DIFFERENCES
                        stops after MAX_DIFFERENCES different layers are found
  -l MAX_LAYER, --max_layer MAX_LAYER
                        only compares until given layer (exclusive, starting
                        at 0)
  -v, --verbose         print differences between files (as well as their
                        names)
</pre>

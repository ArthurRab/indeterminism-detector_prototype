# indeterminism-detector_prototype
Tool to detect which files cause indeterminism in the building of docker images.

Use: ./idd.sh tarball1.tar tarball2.tar

WARNING: Do not use the test_pckgs_reproducibility macro in the root folder of a
workspace, it will fail due to a bug in the download_pkgs rule in base-images-docker
(Instead, use it in a BUILD in a folder in your workspace)

load("@base_images_docker//package_managers:download_pkgs.bzl", "download_pkgs")
load("@base_images_docker//package_managers:install_pkgs.bzl", "install_pkgs")

def test_pckgs_reproducibility(name, packages, base = "@debian8"):
    to_test = []
    for package in packages:
        download_pkgs(
            name = "download_" + package + "_for_reproducibility_test",
            packages = [package],
            image_tar = base,
        )

        install_pkgs(
            name = "install_" + package + "_for_reproducibility_test_1",
            installables_tar = "download_" + package + "_for_reproducibility_test",
            image_tar = base,
            output_image_name = "duplicate",
        )

        install_pkgs(
            name = "install_" + package + "_for_reproducibility_test_2",
            installables_tar = "download_" + package + "_for_reproducibility_test",
            image_tar = base,
            output_image_name = "duplicate",
        )

        to_test += ["install_" + package + "_for_reproducibility_test_1", "install_" + package + "_for_reproducibility_test_2"]

    native.genrule(
        name = name,
        srcs = ["run_idd_on_all_targets.sh", "idd.sh"] + to_test,
        cmd = "sh run_idd_on_all_targets.sh idd.sh $@" + " ".join(["$(location " + file + ")" for file in to_test]),
        outs = ["log.txt"],
    )

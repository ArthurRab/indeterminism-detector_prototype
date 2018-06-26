load("@base_images_docker//package_managers:download_pkgs.bzl", "download_pkgs")
load("@base_images_docker//package_managers:install_pkgs.bzl", "install_pkgs")

def test_pckgs_reproducibility(name, packages, base = "@debian8//image"):
    to_test = []
    for package in packages:
        download_pkgs(
            name = "download_" + package + "_for_reproducibility_test",
            packages = [package],
            image_tar = base,
        )
        for i in ["1", "2"]:
            install_pkgs(
                name = "install_" + package + "_for_reproducibility_test_" + i,
                installables_tar = ":download_" + package + "_for_reproducibility_test.tar",
                image_tar = base,
                output_image_name = "duplicate",
            )

            to_test += [":install_" + package + "_for_reproducibility_test_" + i]

    native.genrule(
        name = name,
        srcs = ["//:run_idd_on_all_targets.sh", "//:idd.sh"] + to_test,
        cmd = "sh $(location //:run_idd_on_all_targets.sh) $(location //:idd.sh) $@ " + " ".join(["$(location " + file + ")" for file in to_test]),
        outs = ["log.txt"],
    )

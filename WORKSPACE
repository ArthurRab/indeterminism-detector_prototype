http_archive(
    name = "bazel_toolchains",
    sha256 = "9b289a6381ff8dd743bd1f22b99fcdd8341c129d44efc910f2b7b4fa2c6dd23e",
    strip_prefix = "bazel-toolchains-50e35b4664a575d326fe27da2b7f1f90e2d6ef51",
    urls = [
        "https://github.com/bazelbuild/bazel-toolchains/archive/50e35b4664a575d326fe27da2b7f1f90e2d6ef51.tar.gz",
    ],
)

load(
    "@bazel_toolchains//repositories:repositories.bzl",
    bazel_toolchains_repositories = "repositories",
)

bazel_toolchains_repositories()

load(
    "@io_bazel_rules_docker//container:container.bzl",
    container_repositories = "repositories",
    "container_pull",
)

container_repositories()

container_pull(
    name = "debian8",
    digest = "sha256:943025384b0efebacf5473490333658dd190182e406e956ee4af65208d104332",
    registry = "gcr.io",
    repository = "cloud-marketplace/google/debian8",
)

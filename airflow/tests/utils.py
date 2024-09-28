import os


def build_test_base_path():
    return "/".join(os.path.dirname(os.path.realpath(__file__)).split("/"))

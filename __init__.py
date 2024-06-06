import sys
import os

from . import env


def update_path() -> None:

    # Local and prod builds have different package directories
    relative_packages_dir = (
        "vendor" if env.environment == "PROD" else "env/lib/python3.11/site-packages"
    )

    packages_dir = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), relative_packages_dir
    )

    sys.path.append(packages_dir)


update_path()

from .src import main

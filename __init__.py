import sys
import os


def update_path() -> None:
    # Nonsense to allow importing from site-packages
    # TODO: need to explicitly vendor here...
    packages_dir = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "env/lib/python3.11/site-packages"
    )

    sys.path.append(packages_dir)


update_path()

from .src import main

import functools
import importlib.metadata


@functools.cache
def get_distribution_metadata() -> importlib.metadata.PackageMetadata:
    """
    Determines and returns metadata for the distribution package that owns
    this import package.

    .. seealso:: https://docs.python.org/3/library/importlib.metadata.html#mapping-import-to-distribution-packages

    """
    assert __package__ is not None
    root_package = __package__.partition(".")[0]
    distributions = importlib.metadata.packages_distributions()[root_package]
    return importlib.metadata.metadata(distributions[0])

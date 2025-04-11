import sys

import nbformat


def remove_kernelspec(filepath):
    with open(filepath, encoding="utf-8") as f:
        notebook = nbformat.read(f, as_version=nbformat.NO_CONVERT)

    # Remove metadata.kernelspec
    if notebook.get("metadata", {}).get("kernelspec"):
        del notebook["metadata"]["kernelspec"]

    # Remove the python version too
    if notebook.get("metadata", {}).get("language_info", {}).get("version"):
        del notebook["metadata"]["language_info"]["version"]

    # Save the cleaned notebook
    with open(filepath, "w", encoding="utf-8") as f:
        nbformat.write(notebook, f)


if __name__ == "__main__":
    for file in sys.argv[1:]:
        remove_kernelspec(file)

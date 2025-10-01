import os
import subprocess

from setuptools import find_packages, setup


def get_long_description():
    with open("README.md", encoding="utf-8") as f:
        text = f.read()

        # replace logo with one that will work on PyPi
        text = text.replace(
            "![Simplini Logo](resources/logo.png)",
            "![Simplini Logo](https://raw.githubusercontent.com/gubenkoved/simplini/main/resources/logo.png)",
        )

        return text


def read_version():
    version_ns = {}
    version_file = os.path.join("src", "simplini", "_version.py")
    with open(version_file, encoding="utf-8") as f:
        exec(f.read(), version_ns)
    return version_ns["__version__"]


def get_git_commit():
    env = os.environ.get("GIT_COMMIT")
    if env:
        return env
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL
        )
        return out.decode("utf-8").strip()
    except Exception:
        return None


commit_hash = get_git_commit()

project_urls = {
    "Homepage": "https://github.com/gubenkoved/simplini",
}

if commit_hash:
    project_urls["Commit"] = (
        f"https://github.com/gubenkoved/simplini/tree/{commit_hash}"
    )


setup(
    name="simplini",
    version=read_version(),
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[],
    python_requires=">=3.7",
    author="Eugene Gubenkov",
    author_email="gubenkoved@gmail.com",
    description="A simple INI file parser/writer",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    keywords="ini, config, parser",
    url="https://github.com/gubenkoved/simplini",
    project_urls=project_urls,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)

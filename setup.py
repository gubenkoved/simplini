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


def get_git_commit():
    """Return git commit hash or None if not available.

    Preference order:
    1) Environment variable GIT_COMMIT (first 7 chars)
    2) `git rev-parse --short HEAD`
    """
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
    version=os.environ.get("PACKAGE_VERSION", "0.0.1+dev"),
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[],
    python_requires=">=3.10",
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
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)

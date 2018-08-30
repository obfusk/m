from pathlib import Path
from setuptools import setup

import m

long_description    = Path(__file__).with_name("README.rst").read_text()

setup(
  name              = "mmm",
  url               = "https://github.com/obfusk/m",
  description       = "minimalistic media manager",
  long_description  = long_description,
  version           = m.__version__,
  author            = "Felix C. Stegerman",
  author_email      = "flx@obfusk.net",
  license           = "GPLv3+",
  classifiers       = [
    "Development Status :: 4 - Beta",
    "Environment :: Console",
    "Intended Audience :: End Users/Desktop",
    "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
    "Operating System :: POSIX :: Linux",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.5",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: Implementation :: CPython",
    "Programming Language :: Python :: Implementation :: PyPy",
    "Topic :: Multimedia :: Video",
    "Topic :: Utilities",
  ],
  keywords          = "media video vlc mpv",
  py_modules        = ["m"],
  entry_points      = { "console_scripts": ["m=m:main_"] },
  python_requires   = ">=3.5",
  extras_require    = { "test": ["coverage"] },
)

'''
    This file is part of Prolothar-Process-Discovery (More Info: https://github.com/shs-it/prolothar-process-discovery).


    Prolothar-Process-Discovery is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.


    Prolothar-Process-Discovery is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.


    You should have received a copy of the GNU General Public License
    along with Prolothar-Process-Discovery. If not, see <https://www.gnu.org/licenses/>.
'''


#import order is important!
import pathlib
from setuptools import setup, find_namespace_packages
import os
import platform
from distutils.extension import Extension
from Cython.Build import cythonize
# The directory containing this file
HERE = pathlib.Path(__file__).parent


# The text of the README file
README = (HERE / "README.md").read_text()
LICENSE = (HERE / "LICENSE").read_text()


with open(HERE / 'requirements.txt', 'r') as f:
    install_reqs = [
        s for s in [
            line.split('#', 1)[0].strip(' \t\n') for line in f
        ] if s != ''
    ]


with open(HERE / 'version.txt', 'r') as f:
    version = f.read().strip()


def make_extension_from_pyx(path_to_pyx: str, include_dirs = None, use_openmp: bool = False) -> Extension:
    extra_compile_args = []
    extra_link_args = []
    if use_openmp:
        if platform.system() == 'Windows':
            extra_compile_args.append('/openmp')
            extra_link_args.append('/openmp')
        else:
            extra_compile_args.append('-fopenmp')
            extra_link_args.append('-fopenmp')


    return Extension(
        path_to_pyx.replace('/', '.').replace('.pyx', ''),
        sources=[path_to_pyx.replace('/', os.path.sep)], language='c++',
        include_dirs=include_dirs,
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args)


if os.path.exists('prolothar_process_discovery/discovery/proseqo/cover_streams/move_stream.pyx'):
    extensions = [
        make_extension_from_pyx("prolothar_process_discovery/discovery/proseqo/greedy_cover.pyx"),
        make_extension_from_pyx("prolothar_process_discovery/discovery/proseqo/cover.pyx"),
        make_extension_from_pyx("prolothar_process_discovery/discovery/proseqo/mdl_score.pyx"),
        make_extension_from_pyx("prolothar_process_discovery/discovery/proseqo/pattern_dfg.pyx"),
        make_extension_from_pyx("prolothar_process_discovery/discovery/proseqo/pattern/pattern.pyx"),
        make_extension_from_pyx("prolothar_process_discovery/discovery/proseqo/pattern/singleton.pyx"),
        make_extension_from_pyx("prolothar_process_discovery/discovery/proseqo/cover_streams/move_stream.pyx"),
        make_extension_from_pyx("prolothar_process_discovery/discovery/proseqo/cover_streams/pattern_stream.pyx"),
        make_extension_from_pyx("prolothar_process_discovery/discovery/proseqo/cover_streams/meta_stream.pyx"),
        make_extension_from_pyx("prolothar_process_discovery/discovery/proseqo/covering_pattern/covering_pattern.pyx"),
        make_extension_from_pyx("prolothar_process_discovery/discovery/proseqo/covering_pattern/covering_singleton.pyx"),
        make_extension_from_pyx("prolothar_process_discovery/discovery/proseqo/covering_pattern/covering_sequence.pyx"),
        make_extension_from_pyx("prolothar_process_discovery/discovery/proseqo/covering_pattern/covering_optional.pyx"),
        make_extension_from_pyx("prolothar_process_discovery/discovery/proseqo/covering_pattern/covering_loop.pyx"),
        make_extension_from_pyx("prolothar_process_discovery/discovery/proseqo/covering_pattern/covering_choice.pyx"),
        make_extension_from_pyx("prolothar_process_discovery/discovery/proseqo/covering_pattern/covering_parallel.pyx"),
        make_extension_from_pyx("prolothar_process_discovery/discovery/proseqo/covering_pattern/covering_inclusive_choice.pyx"),
        make_extension_from_pyx("prolothar_process_discovery/discovery/proseqo/covering_pattern/covering_subgraph.pyx"),
        make_extension_from_pyx("prolothar_process_discovery/discovery/proseqo/covering_pattern/covering_blob.pyx"),
    ]
else:
    extensions = []


cython_profiling_activated = os.environ.get('CYTHON_PROFILING', 'False') == 'True'
print(f'cython_profiling_activated={cython_profiling_activated}')
setup(
    name="prolothar-process-discovery",
    version=version,
    description="algorithms for process mining and data mining on event sequences",
    long_description=README,
    long_description_content_type="text/markdown",
    license=LICENSE,
    url="https://github.com/shs-it/prolothar-process-discovery",
    author="Boris Wiegand",
    author_email="boris.wiegand@stahl-holding-saar.de",
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
    packages=find_namespace_packages(
        include=['prolothar_process_discovery*']
    ),
    include_package_data=True,
    package_data={
            "prolothar_process_discovery": ['*','*/*','*/*/*','*/*/*/*','*/*/*/*/*',
                             '*/*/*/*/*/*','*/*/*/*/*/*/*','*/*/*/*/*/*/*/*']
    },
    exclude_package_data={
            "": ['*.pyc']
    },
    ext_modules=cythonize(
        extensions, language_level = "3", annotate=True,
        compiler_directives={
            'profile': cython_profiling_activated,
        }
    ),
    zip_safe=False,
    install_requires=install_reqs
)

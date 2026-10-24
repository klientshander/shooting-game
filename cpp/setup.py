from pathlib import Path

from setuptools import setup
from pybind11.setup_helpers import Pybind11Extension, build_ext

cpp_dir = Path(__file__).parent


setup(
    name="cosmic-rift-collision",
    version="1.0.0",
    ext_modules=[
        Pybind11Extension(
            "_collision_engine",
            [str(cpp_dir / "collision_engine.cpp"), str(cpp_dir / "bindings.cpp")],
            include_dirs=[str(cpp_dir)],
            cxx_std=17,
        )
    ],
    cmdclass={"build_ext": build_ext},
)

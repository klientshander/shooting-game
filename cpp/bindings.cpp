#include "collision_engine.h"

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;

PYBIND11_MODULE(_collision_engine, module) {
    module.doc() = "Optional C++ circle-collision accelerator for COSMIC RIFT";
    module.def("circle_collisions", &circle_collisions,
               "Find intersecting circle index pairs.",
               py::arg("first"), py::arg("second"));
}

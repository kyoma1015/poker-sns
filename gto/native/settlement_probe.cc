// Test-only bridge into the exact preserved Ledger header used by G12 variants.
// It does not replace or alter that header or the public solver API.
#include "g11_rules_embed.h"
namespace py = pybind11;
PYBIND11_MODULE(pokerid_settlement_probe, m) {
  py::class_<pokerid7rules::Ledger>(m, "Ledger")
      .def(py::init<py::list, py::dict>())
      .def("legal", &pokerid7rules::Ledger::legal)
      .def("act", &pokerid7rules::Ledger::act)
      .def("next_round", &pokerid7rules::Ledger::next_round)
      .def("audit", &pokerid7rules::Ledger::audit)
      .def("settle", &pokerid7rules::Ledger::settle);
  m.def("rank7", &pokerid7rules::rank7);
}

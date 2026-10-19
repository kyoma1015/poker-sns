// G12 P0 prototype: stable importance ratio, distinct solver/checkpoint version.
#pragma once
#include <cmath>
#include <limits>
#include <stdexcept>
namespace pokerid12 {
inline double stable_ratio(double value,long double target,long double sample) {
  if (!std::isfinite(value) || !std::isfinite(target) || !std::isfinite(sample) ||
      target < 0 || sample <= 0) throw std::runtime_error("G12 invalid importance operands");
  if (value == 0 || target == 0) return 0;
  // Exact cancellation avoids subnormal intermediate underflow and rounding.
  if (target == sample) return value;
  int ev=0, et=0, es=0;
  double mv=std::frexp(value,&ev);
  long double mt=std::frexp(target,&et), ms=std::frexp(sample,&es);
  // All mantissas are in [0.5,1) by magnitude: no premature underflow.
  long double mantissa=(static_cast<long double>(mv)*mt)/ms;
  long double result=std::ldexp(mantissa,ev+et-es);
  double output=static_cast<double>(result);
  if (!std::isfinite(result) || !std::isfinite(output) || output==0)
    throw std::runtime_error("G12 importance result not representable as double");
  return output;
}
}

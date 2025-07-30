#pragma once

#include "config.h"

class Smoothing {
public:
  double smoothArray[SMOOTH_NUM];
  double smoothSum{ 0 };

  void addValue(double val);
  double getValue();
};

void Smoothing::addValue(double val) {
  smoothSum -= smoothArray[0];
  smoothSum += val;
  for (int i = 0; i < SMOOTH_NUM - 1; ++i) {
    smoothArray[i] = smoothArray[i + 1];
  }
  smoothArray[SMOOTH_NUM - 1] = val;
}

double Smoothing::getValue() {
  return smoothSum / SMOOTH_NUM;
}
#pragma once

#include <cstddef>
#include <utility>
#include <tuple>
#include <vector>

using Circle = std::tuple<double, double, double>;
using CollisionPair = std::pair<std::size_t, std::size_t>;

std::vector<CollisionPair> circle_collisions(
    const std::vector<Circle>& first,
    const std::vector<Circle>& second);

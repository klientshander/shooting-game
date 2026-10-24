#include "collision_engine.h"

#include <cmath>
#include <tuple>

std::vector<CollisionPair> circle_collisions(
    const std::vector<Circle>& first,
    const std::vector<Circle>& second) {
    std::vector<CollisionPair> result;
    for (std::size_t i = 0; i < first.size(); ++i) {
        const auto& [x1, y1, r1] = first[i];
        for (std::size_t j = 0; j < second.size(); ++j) {
            const auto& [x2, y2, r2] = second[j];
            const double dx = x1 - x2;
            const double dy = y1 - y2;
            const double radius = r1 + r2;
            if (dx * dx + dy * dy <= radius * radius) {
                result.emplace_back(i, j);
            }
        }
    }
    return result;
}

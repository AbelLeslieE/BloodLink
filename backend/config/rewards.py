"""Central reward and badge policy for confirmed blood donations."""

from __future__ import annotations

POINTS_PER_CONFIRMED_DONATION = 100


def badge_for(total_points: int, donation_count: int) -> str:
    """Return the highest badge earned by a donor."""
    if donation_count >= 10 or total_points >= 1000:
        return "Gold Donor"
    if donation_count >= 5 or total_points >= 500:
        return "Silver Donor"
    if donation_count >= 3 or total_points >= 300:
        return "Bronze Donor"
    if donation_count >= 1 or total_points >= 100:
        return "Life Saver"
    return "New Donor"

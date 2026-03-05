import { User } from "../models/User";

const BADGE_THRESHOLDS = [
  { name: "First Ride", condition: (u: any) => u.totalRides >= 1 },
  { name: "Eco Starter", condition: (u: any) => u.co2Saved >= 500 },
  { name: "Green Warrior", condition: (u: any) => u.co2Saved >= 5000 },
  { name: "Ride Veteran", condition: (u: any) => u.totalRides >= 50 },
  { name: "Carbon Hero", condition: (u: any) => u.co2Saved >= 25000 },
  { name: "Road Master", condition: (u: any) => u.totalDistance >= 1000 },
  { name: "Community Star", condition: (u: any) => u.totalRides >= 100 },
  { name: "Planet Saver", condition: (u: any) => u.co2Saved >= 100000 },
];

export async function updateGreenScore(userId: string, rideCo2Saved: number, rideDistanceKm: number) {
  const user = await User.findById(userId);
  if (!user) return null;

  user.totalRides += 1;
  user.totalDistance += rideDistanceKm;
  user.co2Saved += rideCo2Saved;

  // Green score formula: log-scaled CO2 savings + ride frequency bonus
  const co2Factor = Math.log10(Math.max(user.co2Saved, 1)) * 25;
  const rideBonus = Math.min(user.totalRides * 2, 200);
  const distBonus = Math.min(user.totalDistance * 0.1, 100);
  user.greenScore = Math.round(co2Factor + rideBonus + distBonus);

  // Check badges
  const newBadges: string[] = [];
  for (const badge of BADGE_THRESHOLDS) {
    if (!user.badges.includes(badge.name) && badge.condition(user)) {
      user.badges.push(badge.name);
      newBadges.push(badge.name);
    }
  }

  await user.save();
  return { greenScore: user.greenScore, newBadges };
}

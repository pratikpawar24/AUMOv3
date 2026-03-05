import { Request, Response } from "express";
import { Ride } from "../models/Ride";
import { AuthRequest } from "../middleware/auth";
import { updateGreenScore } from "../services/greenScore.service";
import * as ai from "../services/ai.service";

export async function createRide(req: AuthRequest, res: Response) {
  try {
    const ride = await Ride.create({ ...req.body, driver: req.userId });
    res.status(201).json({ ride });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
}

export async function getRides(_req: Request, res: Response) {
  try {
    const rides = await Ride.find({ status: "pending" })
      .sort({ departureTime: 1 })
      .populate("driver", "name avatar greenScore")
      .limit(50);
    res.json({ rides });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
}

export async function getRideById(req: Request, res: Response) {
  try {
    const ride = await Ride.findById(req.params.id)
      .populate("driver", "name avatar greenScore phone")
      .populate("passengers", "name avatar");
    if (!ride) return res.status(404).json({ error: "Ride not found" });
    res.json({ ride });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
}

export async function joinRide(req: AuthRequest, res: Response) {
  try {
    const ride = await Ride.findById(req.params.id);
    if (!ride) return res.status(404).json({ error: "Ride not found" });
    if (ride.seatsAvailable <= 0) return res.status(400).json({ error: "No seats available" });
    if (ride.passengers.includes(req.userId as any)) return res.status(400).json({ error: "Already joined" });

    ride.passengers.push(req.userId as any);
    ride.seatsAvailable -= 1;
    await ride.save();

    res.json({ ride });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
}

export async function completeRide(req: AuthRequest, res: Response) {
  try {
    const ride = await Ride.findById(req.params.id);
    if (!ride) return res.status(404).json({ error: "Ride not found" });

    ride.status = "completed";
    await ride.save();

    // Update green scores for all participants
    const allUsers = [ride.driver.toString(), ...ride.passengers.map((p) => p.toString())];
    const co2PerPerson = ride.co2Saved / Math.max(allUsers.length, 1);

    for (const uid of allUsers) {
      await updateGreenScore(uid, co2PerPerson, ride.distanceKm);
    }

    res.json({ ride });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
}

export async function searchRides(req: Request, res: Response) {
  try {
    const { origin_lat, origin_lng, dest_lat, dest_lng, departure_time } = req.query;
    const rides = await Ride.find({ status: "pending" })
      .populate("driver", "name avatar greenScore")
      .limit(30);

    // If AI service is available, use it for matching
    if (origin_lat && dest_lat) {
      try {
        const offers = rides.map((r) => ({
          id: r._id.toString(),
          driver_id: r.driver._id?.toString() || r.driver.toString(),
          origin_lat: r.origin.lat,
          origin_lng: r.origin.lng,
          dest_lat: r.destination.lat,
          dest_lng: r.destination.lng,
          departure_time: r.departureTime.toISOString(),
          seats_available: r.seatsAvailable,
          route_distance_km: r.distanceKm || 10,
          route_duration_min: r.durationMin || 25,
          preferences: r.preferences || {},
        }));

        const matchResult = await ai.matchRides({
          request: {
            passenger_id: "search",
            origin_lat: Number(origin_lat),
            origin_lng: Number(origin_lng),
            dest_lat: Number(dest_lat),
            dest_lng: Number(dest_lng),
            departure_time: (departure_time as string) || new Date().toISOString(),
            preferences: {},
          },
          offers,
          top_k: 10,
        });

        return res.json({ rides, matches: matchResult.matches });
      } catch {
        // Fallback to plain rides if AI is unavailable
      }
    }

    res.json({ rides });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
}

export async function getMyRides(req: AuthRequest, res: Response) {
  try {
    const driven = await Ride.find({ driver: req.userId }).sort({ createdAt: -1 }).limit(20);
    const joined = await Ride.find({ passengers: req.userId }).sort({ createdAt: -1 }).limit(20);
    res.json({ driven, joined });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
}

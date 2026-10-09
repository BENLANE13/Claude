# Fun Features for the BODE App (proposals)

Campus Wars was dropped. These ideas make each ride fun on its own instead of turning it into a school-vs-school contest. Most are personal or between friends. Each one uses something only BODE has: a drone overhead, the sun's position, or your walk map.

Effort: **S** = days of app work, **M** = weeks, **L** = needs new drone hardware or flight behavior.

## Top picks (build these first)

### 1. BODE Shot (overhead photo) · M
At the end of a ride, tap "BODE Shot" and the drone rises a few meters and takes one top-down photo of you (and friends) standing in its violet shadow. The photo goes straight to your phone and is never stored by BODE.
- **Why it's fun:** nobody else can give you an overhead shot of yourself on the way to class. It's built for Instagram and TikTok, which makes it free marketing.
- **Guardrails:** opt-in per photo, a countdown so everyone in frame knows, and blurred faces for anyone who didn't tap.

### 2. Meet the Fleet (collectible drones) · S
Every BODE has a name and a personality on its unlock screen: *Ziggy, likes golden hour*; *Mochi, has a top speed of 8 m/s*. Your profile keeps a "BODEdex" of every drone you've ridden with. Rare drones (a gold-rim BODE, a seasonal one) show up now and then.
- **Why it's fun:** a reason to unlock a different drone, a little Pokémon-style collecting, and drones that feel like characters instead of machines.

### 3. Your Summer Shade Wrapped · S
An end-of-semester recap, Spotify Wrapped style: total km walked in shade, hottest day you rode, the time of day you rode most, your favorite drone, and your most-walked route drawn as a glowing line on the map.
- **Why it's fun:** a shareable story card. It reuses data the app already tracks (path, distance, shade-minutes).

### 4. Shade Buddy (two riders, one BODE) · M
Walk with a friend under one canopy and split the fare. The app shows a "stay close" ring, since the 1 m canopy can shade two people walking side by side.
- **Why it's fun:** walking to class with someone is more fun, and splitting it makes each ride cheaper.
- **Engineering note:** the shade solver needs to aim at the midpoint of two heads. That's a small change to `bode_shade`.

## More ideas

### 5. Canopy Colors · M (needs LED rim)
An LED ring around the canopy rim lets you pick your ride's glow color, so friends can spot "your" BODE across the quad. Seasonal and unlockable patterns. The canopy itself stays Eclipse Violet.

### 6. Wave Hello · M
Wave at your BODE and it does a little bob in reply. A thumbs-up ends the ride, and a "stop" palm makes it hold position. Gestures are recognized on the drone's camera, on-device.

### 7. Sun Quests · S
Optional personal challenges tied to the real sun: "Ride at solar noon" (the app shows the exact minute), "Walk 1 km on a 100°F day", "Catch golden hour on your way home". Quests award badges and occasional free minutes.
- **Why it's fun:** it teaches people where the sun is in a playful way. The app already calculates solar noon to the minute.

### 8. Shade Drops · S
A few times a week, a "Shade Drop" appears on the map: the first rider to unlock the marked BODE gets a free ride. It's a light treasure hunt that also nudges riders toward under-used Roosts, which helps the fleet balance itself.

### 9. Route Art · S
Your walk path is drawn on the map, so let people draw with it: walk a heart, a smiley, or your initials around campus, and the app saves it as art (like Strava GPS art).

### 10. "Degrees Cooler" counter · S
After each ride: "You dodged 14 minutes of direct sun, and it felt about 10–15°F cooler under BODE." The exact number should be calibrated against real temperature measurements under the canopy before we show it.

## What to avoid
- **Anything that rewards speed or distance races.** Running under a drone is unsafe, and the app already ignores segments faster than 6 m/s.
- **Public rankings of people.** Location history is sensitive, so keep comparisons to friends who opt in.
- **Features that keep the drone out longer than the walk.** Every minute in the air costs battery and fleet time.

## Suggested order
1. **Pilot (cheap and data-driven):** Meet the Fleet, Sun Quests, Route Art, and Shade Drops (all **S**).
2. **End of first semester:** Summer Shade Wrapped.
3. **Once flight software is mature:** BODE Shot and Shade Buddy.
4. **Hardware v2:** Canopy Colors and Wave Hello.

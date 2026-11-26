# Bubble Wash Kingdom - full-video coverage checklist (Level 1, approved gameplay video 25982.mp4)

Owner requirement (2026-11-26): the WHOLE 15 s approved Google Flow gameplay video is the blueprint for the playable game.
Every section below must reach at least 9/10 on its own; one good hero screen is not enough. Hero screen first, then
section by section, reusing approved assets. Text only in this file (the repo is public): reference frames, video and
side-by-side sheets stay private in `Reference/` and `Captures/sections/`.

Camera rule for gameplay: the video switches to a FRONT camera from 3.75 s. In the game the player always sees the
mascot from BEHIND (approved hero camera); the front-camera parts of the video define the SCENERY of each section, and
front views are only used for the celebration / portal finale.

Unity track: 14 m (start) -> ~351 m (portal), one continuous ride, no cuts. Stills = `Captures/stills/` (CaptureStillsBatch).

| # | Video | Section | Unity track (stills) | Score r5 base (09:15) | Owner domains |
|---|-------|---------|----------------------|-----------------------|---------------|
| S1 | 0.00-1.25 s | Opening machine hall | 14-40 m (01_hall_start 16, 02_hall_curve 36) | 3/10 | env, water, light |
| S2 | 1.25-3.25 s | Rainbow slide into the gold tunnel mouth (hero frame 3.0 s) | 40-110 m (03_tunnel_entry 55, hero 105.5) | hero 5.5-6/10, 2.0 s view 3.5/10 | all |
| S3 | 3.25-5.75 s | Tunnel of gold bulb rings and neon stars | 110-170 m (04_tunnel 92, 05 lane L 128, C1 100) | 5/10 | env, light |
| S4 | 6.00-7.00 s | Tunnel bend, first sock-chamber window, coin line | 170-205 m (06 lane R 170) | 4/10 | env, water |
| S5 | 7.00-9.00 s | Sock chambers and pink glass pipes | 205-240 m (07_chambers 215, C2 220) | 3.5/10 | env, water, light |
| S6 | 9.00-12.75 s | Chamber tunnel 2: windows both sides, cyan water pipe, dense stars | 240-310 m (08_sweep 250) | 4/10 | env, water, light |
| S7 | 12.75-15.00 s | Golden light portal finale | 310-351 m (09_portal 317, C3 329) | 4.5/10 | env, light, water |
| ALL | 0-15 s | The mascot (same character everywhere) | every frame | 4/10 in game (old model); v4 candidate 6/10 in Blender, not approved | character |

Whole-game estimate at the r5 base: ~4/10 (hero screen ~5.5-6/10).

## Section details (what must be there)

### S1 Opening machine hall (0.00-1.25 s)
- Camera in the video: high rear three-quarter from the upper left; the slide curves right into the tunnel mouth.
- Must have: pink washing-machine console with screens (t-shirt icon) and a gold paw emblem (upper left); big fluffy
  pink / white / blue brush rollers (top centre, spinning); polished gold machinery, pipes and valves; glowing cyan glass
  pipe (left); gold rings with warm bulbs framing the tunnel mouth; rainbow slide (pink, cyan, yellow lanes, glossy rails)
  with blue water and glowing cyan chevrons; gold paw coins and purple gems along the slide; soft foam banks; bubbles.
- Character: seen from behind / three-quarter, arms out, kicking feet, splash at the feet.
- Unity now: mostly empty purple space, large smooth white cloud blobs, one blurry roller, a purple pillar; no console,
  no gold machinery, no cyan pipe; slide is pink only.

### S2 Rainbow slide into the gold tunnel mouth (1.25-3.25 s, HERO 3.0 s)
- Camera: moves directly behind the mascot (= our gameplay camera). Rollers drift to the upper left, gold tunnel ring with
  bulbs ahead/right, coins pass close on the left, pink + yellow lanes, cyan chevrons, milky splash crowns both sides,
  foam banks on the left, first neon stars inside the tunnel.
- Unity now: hero is the closest section (tunnel, rings, stars, arrows); rings too centred/telescope-like, splash crowns
  are flat perforated white sheets, cloud-like foam blobs, old mascot (hat hides the body). The 2.0 s view (hall end)
  lacks the rollers, machinery and rainbow lanes.

### S3 Tunnel of gold bulb rings and neon stars (3.25-5.75 s)
- Video: front camera; purple-grey drum walls with columns of dark oval perforations; big cyan, yellow and pink neon
  tube stars; gold rings with bulbs receding; pink rails; foam banks on both sides; chevron under the mascot.
- Unity now: rings and perforated walls exist; stars too few and small; holes small and flat; foam = smooth blobs.

### S4 Tunnel bend, first chamber window (6.00-7.00 s)
- Video: the tunnel banks; a round gold-framed porthole on the left wall shows a rainbow and colourful striped socks;
  a line of gold coins on the right; pink / yellow / cyan stars.
- Unity now: no porthole at this distance; coins are present but as big flat discs; cloud blobs.

### S5 Sock chambers and pink glass pipes (7.00-9.00 s)
- Video: big round chamber windows (gold frames, hinges) with swirling water, rainbows and floating socks on the left;
  vertical glass pipes with glowing pink liquid; dense neon stars; coins on the right wall; pink gem; bubbles.
- Unity now: chambers exist as models but read small / off-screen; no glowing pink pipes in view; white cloud banks.

### S6 Chamber tunnel 2 (9.00-12.75 s)
- Video: chamber windows on both sides (big rainbow-sock chamber left), a flowing cyan glass water pipe on the left,
  dense stars on both walls, bulb rings, foam banks both sides, milky crown splashes, the mascot squints with joy.
- Unity now: one porthole at the right edge, cloud banks, flat splash sheets, few stars.

### S7 Golden light portal finale (12.75-15.00 s)
- Video: a golden starburst portal opens behind/around a big gold bulb ring; sparkle stars; the cyan glass pipe curves
  on the left; rainbow chamber on the left; the light fills the frame at the end.
- Unity now: a yellow glow disc at the tunnel end with a gold ring; coins on the track; no starburst rays, no sparkles,
  no glass pipe.

## Cross-section problems (fix once, applies everywhere)
1. Mascot: the old in-game model (mushroom hat hiding the body, pale spiky pom-pom, hairy soles) - v4 replaces it after
   owner approval (character).
2. Foam: smooth oversized white cloud blobs -> soft irregular clusters of small foam bubbles (water/FX).
3. Splash crowns: flat perforated white sheets -> thick milky lace with rounded rims, finger tips and drops (water/FX).
4. Slide: pink-only -> glossy rainbow lanes (pink, yellow, cyan) with glossy pink rails (environment + water).
5. Density: the video is far busier and brighter (machinery, stars, coins, bubbles, chambers) - avoid empty repeated
   purple tunnel stretches (environment + lighting).
6. Rings: polished bevelled gold with small warm bulbs, receding off-centre along the curve (environment + lighting).

## Gameplay verification (Play Mode autopilot test, r5 base 09:21)
- Whole track 14 -> 350.4 m finished in one continuous run; 8/8 tests passed; rear-camera checks 639, violations 0;
  coins collected 96, gems 3; recording `Captures/playmode/gameplay_autopilot_9x16.mp4`.
- Editor batch FPS on this laptop (not a device measurement): avg 53.7, 1 % low 39.3. Render counters (draw calls,
  triangles) are not reported in editor batch mode; the last standalone measurement (2026-11-25) showed up to 4350 draw
  calls and 2.14 M triangles - far above a mobile budget. Android: not built, not tested (5.2 GB disk free).
- Not yet verified per section: obstacle collisions, jump timing, swipe feel on a touch screen.

## Order of work
1. Hero screen (S2) to the owner's approval: mascot v4 approval + integration, splash/foam, rings, lighting.
2. S1 opening hall (most different today), then S3 -> S7 in order, reusing the approved hero assets.
3. Per section after each round: private sheet `Captures/sections/S<n>_ref_vs_unity_<round>.png` (reference frame |
   Unity screenshot), honest score, differences, completed, remaining, gameplay status - updated in this file.
4. Mobile budget pass (draw calls, triangles, fur shells) once the look of a section is approved.

# Bubble Wash Kingdom - full-video coverage checklist (Level 1, approved gameplay video 25982.mp4)

Owner requirement (2026-11-26): the WHOLE 15 s approved Google Flow gameplay video is the blueprint for the playable game.
Every section below must reach at least 9/10 on its own; one good hero screen is not enough. Hero screen first, then
section by section, reusing approved assets. Text only in this file (the repo is public): reference frames, video and
side-by-side sheets stay private in `Reference/` and `Captures/sections/`.

Camera rule for gameplay: the video switches to a FRONT camera from 3.75 s. In the game the player always sees the
mascot from BEHIND (approved hero camera); the front-camera parts of the video define the SCENERY of each section, and
front views are only used for the celebration / portal finale.

Unity track: 14 m (start) -> ~351 m (portal), one continuous ride, no cuts. Stills = `Captures/stills/` (CaptureStillsBatch).

| # | Video | Section | Unity track (comparison still) | Score r5 (10:03 build) | Owner domains |
|---|-------|---------|--------------------------------|------------------------|---------------|
| S1 | 0.00-1.25 s | Opening machine hall | 14-40 m (01_hall_start 16 m, rear) | 3/10 | env, water, light |
| S2 | 1.25-3.25 s | Rainbow slide into the gold tunnel mouth (HERO 3.0 s) | 40-110 m (hero 105.5 m, rear) | hero 9:16 ~6/10 (16:9 view 5/10) | all |
| S3 | 3.25-5.75 s | Tunnel of gold bulb rings and neon stars | 110-170 m (C1 100 m, front) | 3.5/10 | env, light |
| S4 | 6.00-7.00 s | Tunnel bend, first sock-chamber window, coin line | 170-205 m (C4 190 m, front) | 3/10 | env, water |
| S5 | 7.00-9.00 s | Sock chambers and pink glass pipes | 205-240 m (C2 220 m, front) | 3/10; r6 8.25 s shot test (front, shot-matched) v1 2.5 -> v5 ~4/10, test scene Test_S5_Shot0825 + real-time recording | env, water, light |
| S6 | 9.00-12.75 s | Chamber tunnel 2: windows both sides, cyan water pipe, dense stars | 240-310 m (C5 280 m, front) | 3/10 | env, water, light |
| S7 | 12.75-15.00 s | Golden light portal finale | 310-351 m (09_portal L-34, rear) | 3.5/10 | env, light, water |
| ALL | 0-15 s | The mascot (same character everywhere) | every frame | in game 4/10 (old model; its front face reads badly in C1/C4/C2/C5). v4 Blender master f14 ~6.5/10 (hero/rear 7, front 6.5, side 5.5, face 6), NOT approved. v4 mobile FBX in-game candidate ~4/10: pom-pom renders as a bare dark ball, arms as dark spikes, hat too large - not ready for approval | character |

## Round 8 masters scores (2026-11-26 18:45, build lead_r8m 18:40 = checkpoint-21-r8m) - 3 judges + 1 skeptic (bwk-round7-verify {tag: "r8m"})
Sheets `Captures/sections/S<n>_triptych_r8m.png` (video | r8 17:34 | r8m 18:40). Format: with mascot / scenery only.

| # | r8 (17:34) | r8m (18:40) | Biggest remaining gaps (skeptic) |
|---|------------|-------------|----------------------------------|
| S1 | 5 / 5 | 5 / 5 | huge close gold bulb-ring tunnel mouth missing (small far arches); slide not a saturated rainbow, no right curve; no close coins / gem / cyan pipe / stars |
| S2 | 5.5 / 5.5 | 5.5 / 5.5 | too few, too small neon stars; no upper-left roller, thin foam; sparse big wall holes; far end a pink blur |
| S3 | 4.5 / 5 | 4.5 / 5 | no big near-camera cyan stars; no close bulb-lined ring; flat light-lavender wall |
| S4 | 3.5 / 4 | 3.5 / 4 | porthole with rainbow socks not visible from the FRONT comparison camera (it sees the new doors' backs); oversized coins; no glass pipe |
| S5 | 3.5 / 4 | 3.5 / 4 | same door-back problem; pink pipe only a pale block; oversized coins; few bubbles |
| S6 | 4 / 4.5 | 4 / 4.5 | door backs read as flat lilac slabs; no cyan glass pipe; few stars |
| S7 | 4 / 4.5 | 4.5 / 5 | golden burst is a real gain (+0.5); no rainbow chamber / cyan pipe at the left; no stars / bubbles in the burst |
Whole game: 4.3 -> 4.4 with mascot, 4.6 -> 4.7 scenery only. Verdict: not substantially closer - only S7 moved. KEY FINDING: the
new master doors face the REAR gameplay camera (they read well in the rear stills 07_chambers / 08_sweep) but the S4-S6
comparison stills are FRONT views (R4 / R5 / R6, matched to the video's camera) that see the doors from behind, so the
doors cannot count there. Open decision for the lead / owner: chambers readable from both directions, or rear gameplay
stills added to the S4-S6 judged sheets.

## Round 7 scores (2026-11-26 13:20, build lead_r7_final 13:06) - independent: 3 judges + 1 skeptic (workflow bwk-round7-verify)
Scored from `Captures/sections/S<n>_triptych_r7.png` (video | round 6 | round 7; row 2 = mascot hidden). The skeptic lowered
most judge scores by 0.5. Format: with mascot / scenery only.

| # | Round 6 | Round 7 | Biggest remaining gaps (skeptic) |
|---|---------|---------|----------------------------------|
| S1 | 3.5 / 3.5 | 4 / 4 | no rainbow slide lanes; dim indigo hall instead of bright pink-lilac + warm glow; tunnel mouth small and far |
| S2 | 5 / 5.5 | 5 / 5 | few small stars; far end a soft pink blur (slight regression); sparse big wall holes; no rainbow lanes |
| S3 | 3.5 / 4 | 3.5 / 4 | unchanged in its still (the C1 camera at 100 m looks back at 60-100 m, so the new S3 stars are not in view) |
| S4 | 3.5 / 3.5 | 4 / 4.5 | porthole only a cut-off sliver at the frame top; no glass pipe beside it; near wall stars missing |
| S5 | 3.5 / 3.5 | 4 / 4.5 | no glowing pink glass pipe in view; no big close porthole with socks; no pink gem, few bubbles |
| S6 | 3.5 / 3.5 | 4.5 / 5 | no cyan glass pipe curving down the left wall in view; fewer stars; chamber small with no socks visible |
| S7 | 4 / 4 | 4.5 / 5 | portal small and far (reference: ring + golden burst fill the frame); burst too white; no sparkles |
Whole game: ~3.8 -> ~4.2 with mascot, ~3.9 -> ~4.6 scenery only. Verdict: real but moderate progress; every section still
lacks the rainbow lanes, the bright pink-lilac warm lighting, milky splash crowns, bubbly foam and the right mascot.
Note: several gaps come from the front comparison cameras (C stills: 0.95 m up, FOV 46) framing much less of the upper
tunnel than the video's camera - windows read as slivers at the frame top. Next: reference-matched TEMPORARY comparison
cameras (solved like ShotMatchTool), never the gameplay camera.

Whole-game estimate (10:03 build): ~3.5/10; hero screen ~6/10 (r4 base 07:05 was ~5.5).
Private sheets: `Captures/sections/S1..S7_ref_vs_unity_r5_1003.png`, overview `ALL_ref_vs_unity_r5_1003.png`;
hero triptych reference | 07:05 | 10:03 `Captures/milestones/m5_r5_triptych_ref_0705_1003.png`.
Round 5 completed: lighting pass (polished amber gold + warm bulbs, pink haze on the upper-left wall, bluer lower water,
softer grade); mascot v4 f12-f14 (hat hugs the head, one wide pale-pink stripe, stubby raised arms, smooth white soles
with pink pads, bigger eyes) + first rigged mobile export SK_Mascot_v4.fbx (17 bones, 13 clips, 74.5k triangles) -
not wired into the game; front comparison stills C4/C5 added and coins hidden in front of comparison cameras.

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

## 7.50-15.00 s quarter-second map (owner's reference sheet, 2026-11-26 09:55) -> Unity section
| Video | Section | What the frames show (all must be rebuilt as real 3D) |
|-------|---------|--------------------------------------------------------|
| 7.50-8.00 | S5 | round gold-framed chamber window on the left (rainbow interior, striped socks); vertical transparent PINK pipe with glowing liquid; gold coins on the right wall; pink and yellow tube stars; bulb rings ahead |
| 8.25-8.75 | S5 | pink pipe + rainbow sock chamber left; dense pink stars; pink gem upper right; bubbles; camera banks |
| 9.00-9.75 | S6 | big rainbow chamber left (blue socks), gold hinges / mechanical frame; cyan stars right; bubbles |
| 10.00-10.75 | S6 | two chamber windows left, transparent CYAN pipe curving on the left, stars on both walls, gold bulb ring ahead |
| 11.00-12.00 | S6 | chambers left, cyan stars right, bulb rings, foam banks both sides; mascot squints with joy (blink) |
| 12.00-12.75 | S6 -> S7 | golden light starts at the far end; sparkles; chambers and cyan pipe continue |
| 13.00-13.75 | S7 | golden starburst portal inside a big gold bulb ring; cyan water pipe curving left; rainbow chamber left; cyan stars right |
| 14.00-15.00 | S7 | the portal light fills the frame; bulb ring large; sparkle stars; flowing water pipe; foam and milky crown splashes |

Mascot in 7.5-15 s (front camera): happy open smile, big glossy eyes, blinks / squints with joy (5.75, 11.25-11.75,
12.0-13.5), arms out balancing, leans with the banking slide, feet forward with pink pads, milky crown splash at the
feet. In the game these become: the rear-view slide animation with leans and balance, plus front-facing celebration
moments (portal finale) only.

Comparison sheets per section (private): `bash Tools/section_sheet.sh <tag>` -> `Captures/sections/`.
Front comparison stills: C1 (100 m), C2 (220 m), C3 (L-22) exist; C4 (190 m, S4) and C5 (280 m, S6) are being added.

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

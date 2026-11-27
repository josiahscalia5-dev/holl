using System.Collections.Generic;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace BubbleWash.EditorTools
{
    // OWNER: hall / portal agent (round 7, "environment B"). Implements the two lead hooks declared in SceneBuilder.cs:
    //   BuildHallExtras   - opening machine hall S1 / S2 (track 14-115 m), called right after BuildHallMachinery
    //   BuildPortalExtras - golden starburst portal finale S7 (318-351 m), called right after BuildPortal
    // Shot-matched placement: the S1 rear still camera (CaptureTools "01_hall_start", 16 m, 16:9) is rebuilt with the
    // RunnerCameraRig formulas and the new assets go where reference frame f_00.50s shows them (u, v measured from the
    // top-left of the 1280x720 frame, depth in metres along the view axis). Assets: Tools/Blender/scripts/build_hall_assets.py
    // (*_r7); their display faces are authored toward Blender +Y = asset -Z (toward the oncoming player).
    // Gameplay is untouched: decoration only (no colliders), nothing over the slide below 2.6 m, camera rig unchanged.
    public static partial class SceneBuilder
    {
        struct HallCam { public Vector3 pos; public Quaternion rot; public float tanHalf; public float aspect; }

        /// <summary>The still camera of CaptureTools at track distance d (runner centred, not jumping), from the
        /// RunnerCameraRig formulas (landscape 2.9 / 1.6 / FOV 52 / pitch 9, portrait = the frozen hero values).</summary>
        static HallCam RearStillCam(float d, float aspect)
        {
            float portrait = Mathf.InverseLerp(1.2f, 0.6f, aspect);
            float back = Mathf.Lerp(2.9f, HeroCamBack, portrait);
            float h = Mathf.Lerp(1.6f, HeroCamHeight, portrait);
            float fov = Mathf.Lerp(52f, HeroCamFov, portrait);
            float pitch = Mathf.Lerp(9f, HeroCamPitch, portrait);
            var fc = track.Evaluate(d - back);
            var fr = track.Evaluate(d);
            var fl = track.Evaluate(d + 10f);
            Vector3 pos = fc.position + fc.flatUp * h - Vector3.up * ((fc.position.y - fr.position.y) * 0.85f);
            Vector3 ahead = fl.position + fl.flatUp * h + Vector3.up * ((fr.position.y - fl.position.y) * 0.5f);
            Vector3 look = Vector3.Lerp(ahead, fr.position + fr.flatUp * 0.45f, 0.08f);
            var rot = Quaternion.LookRotation(look - pos, fc.flatUp) * Quaternion.Euler(pitch, 0f, 0f)
                      * Quaternion.Euler(0f, 0f, Mathf.Clamp(-fr.roll * 0.5f, -11f, 11f));
            return new HallCam { pos = pos, rot = rot, tanHalf = Mathf.Tan(fov * 0.5f * Mathf.Deg2Rad), aspect = aspect };
        }

        /// <summary>Screen S2 pass 2 (asset artist): the comparison-only S2 camera of CaptureTools "R2_rear_S2_like_3s"
        /// (mascot at HeroMouthDistance, 2.75 back / 1.0 up / 0.3 right, pitch 6, yaw -9, vFOV 58, 16:9) for shot-matched
        /// placement of what the reference f_03.00s shows around the door. Placement helper only; the rig is unchanged.</summary>
        static HallCam R2Cam()
        {
            var f = track.Evaluate(HeroMouthDistance);
            Vector3 fwd = Vector3.ProjectOnPlane(f.forward, Vector3.up).normalized, right = Vector3.Cross(Vector3.up, fwd);
            Vector3 pos = f.position - fwd * 2.75f + Vector3.up * 1.0f + right * 0.3f;
            var rot = Quaternion.LookRotation(fwd, Vector3.up) * Quaternion.Euler(6f, -9f, 0f);
            return new HallCam { pos = pos, rot = rot, tanHalf = Mathf.Tan(29f * Mathf.Deg2Rad), aspect = 16f / 9f };
        }

        /// <summary>Embedded FBX materials -> the project material of the same name (works before the full build's
        /// model remap, so a new model shows its real materials in an agent preview).</summary>
        static void HallOwnMaterials(GameObject go)
        {
            foreach (var r in go.GetComponentsInChildren<Renderer>())
            {
                var mats = r.sharedMaterials;
                for (int i = 0; i < mats.Length; i++)
                    if (mats[i] != null) { var rep = MaterialLibrary.Get(mats[i].name); if (rep != null) mats[i] = rep; }
                r.sharedMaterials = mats;
            }
        }

        /// <summary>LODGroup over two child meshes of a placed model (LOD1 from 12 % screen height, culled under 1.5 %).</summary>
        static void HallLods(GameObject go, string lod0, string lod1)
        {
            var a = go.transform.Find(lod0);
            var b = go.transform.Find(lod1);
            if (a == null || b == null) return;
            var lg = go.GetComponent<LODGroup>();
            if (lg == null) lg = go.AddComponent<LODGroup>();
            lg.SetLODs(new[]
            {
                new LOD(0.12f, a.GetComponentsInChildren<Renderer>()),
                new LOD(0.015f, b.GetComponentsInChildren<Renderer>()),
            });
            lg.RecalculateBounds();
        }

        /// <summary>World point seen at frame position (u, v) (0..1 from the top-left) at the given view depth.</summary>
        static Vector3 HallScreenPoint(HallCam c, float u, float v, float depth)
        {
            var local = new Vector3((u * 2f - 1f) * c.tanHalf * c.aspect * depth, (1f - 2f * v) * c.tanHalf * depth, depth);
            return c.pos + c.rot * local;
        }

        /// <summary>Upright rotation whose display side (asset -Z) faces the camera, turned by yaw degrees about world up.</summary>
        static Quaternion HallFaceCam(HallCam c, Vector3 at, float yaw = 0f)
        {
            Vector3 away = Vector3.ProjectOnPlane(at - c.pos, Vector3.up);
            if (away.sqrMagnitude < 1e-4f) away = c.rot * Vector3.forward;
            return Quaternion.AngleAxis(yaw, Vector3.up) * Quaternion.LookRotation(away.normalized, Vector3.up);
        }

        /// <summary>Spawns an r7 model so that its local point `anchor` (asset space, metres) lands on `pos`.</summary>
        static GameObject HallPlace(GameObject parent, string group, string name, Vector3 pos, Quaternion rot, float scale,
                                    Vector3 anchor = default, bool isStatic = true)
        {
            var prefab = ModelPrefab(group, name);
            if (prefab == null) { Debug.LogWarning($"[BWK] hall r7: model missing {group}/{name}"); return null; }
            var go = Spawn(prefab);
            go.name = name;
            go.transform.SetParent(parent.transform, false);
            go.transform.localScale = Vector3.one * scale;
            go.transform.SetPositionAndRotation(pos - rot * (anchor * scale), rot);
            foreach (var r in go.GetComponentsInChildren<Renderer>())
            {
                r.shadowCastingMode = ShadowCastingMode.Off;
                r.receiveShadows = true;
            }
            if (isStatic)
                foreach (var t in go.GetComponentsInChildren<Transform>())
                    GameObjectUtility.SetStaticEditorFlags(t.gameObject, StaticEditorFlags.BatchingStatic | StaticEditorFlags.ReflectionProbeStatic);
            return go;
        }

        /// <summary>Roller rotation: hub end (asset +X) along hubDir, gold arm (asset +Y) up.</summary>
        static Quaternion HallRollerRot(Vector3 hubDir)
        {
            hubDir.Normalize();
            Vector3 z = Vector3.Cross(hubDir, Vector3.up).normalized;
            Vector3 y = Vector3.Cross(z, hubDir);
            return Quaternion.LookRotation(z, y);
        }

        /// <summary>r8 v2 (asset artist): raises a roller centre just enough that its fur bottom stays >= minClear above the
        /// slide wherever the roller hangs over the slide corridor (horizontal distance to the centre line < 3 m), sampled
        /// along its axis. SM_BrushRoller_r8: band peak radius 0.98 m and 2.62 m long in asset space, + 0.30 m world fur.</summary>
        static Vector3 HallRollerClear(Vector3 p, Quaternion rot, float scale, float minClear, string label, float corridor = 3f)
        {
            float radius = 0.98f * scale + 0.32f, halfLen = 1.4f * scale, lift = 0f, worst = float.MaxValue;
            for (int i = -4; i <= 4; i++)
            {
                Vector3 q = p + rot * Vector3.right * (halfLen * i / 4f);
                float bestD = float.MaxValue, slideY = 0f;
                for (float d = 0f; d <= HallMouthD + 12f; d += 0.5f)
                {
                    var f = track.Evaluate(d);
                    Vector3 rel = q - f.position;
                    float hd = new Vector2(rel.x, rel.z).magnitude;
                    if (hd < bestD) { bestD = hd; slideY = f.position.y; }
                }
                if (bestD > corridor) continue;
                float clear = q.y - radius - slideY;
                worst = Mathf.Min(worst, clear);
                lift = Mathf.Max(lift, minClear - clear);
            }
            Debug.Log($"[BWK] hall roller r8 {label}: scale {scale:F2}, min clearance over the slide {(worst == float.MaxValue ? -1f : worst):F2} m, lifted {lift:F2} m");
            return p + Vector3.up * lift;
        }

        /// <summary>Brush roller = spinning bristle body (about its own X axis, like the video) + static gold hub and arm.</summary>
        static void HallRoller(GameObject parent, Vector3 pos, Quaternion rot, float scale, float spin, string bodyVariant = null)
        {
            // r8 (asset artist): smooth plush band body + BWK/Fur shells (M_RollerFur_r8) instead of the r7 box blades;
            // same axis / origin / size, so only the model reference changes (r7 stays the fallback).
            // S2 pass 2: optional body variant (SM_BrushRoller_s2 = same body, pink-dominant bands), materials by slot name.
            string bodyName = ModelPrefab("Machinery", "SM_BrushRoller_r8") != null ? "SM_BrushRoller_r8" : "SM_BrushRoller_r7";
            if (bodyVariant != null && ModelPrefab("Machinery", bodyVariant) != null) bodyName = bodyVariant;
            var body = HallPlace(parent, "Machinery", bodyName, pos, rot, scale, default, false);
            if (body != null) HallOwnMaterials(body);
            HallPlace(parent, "Machinery", "SM_BrushRollerArm_r7", pos, rot, scale);
            if (body == null) return;
            var sp = body.AddComponent<Spinner>();
            sp.localAxis = Vector3.right;
            sp.degreesPerSecond = spin;
        }

        /// <summary>Lavender tower with the paw emblem at world height pawWorld, plus a second tower below so it reaches the
        /// hall floor (the reference towers run out of the frame at the top and disappear in the foam at the bottom).</summary>
        static void HallTower(GameObject parent, Vector3 pawPos, Quaternion rot, float scale)
        {
            var top = HallPlace(parent, "Machinery", "SM_HallPillar_r7", pawPos, rot, scale, new Vector3(0f, 3.15f, -1.1f));
            if (top == null) return;
            HallPlace(parent, "Machinery", "SM_HallPillar_r7", top.transform.position - Vector3.up * 7.3f * scale, rot, scale);
        }

        /// <summary>Round 7 v2: the tunnel mouth (the washing-machine door) stands at 40 m instead of the bare tunnel start
        /// (62 m). In reference 0.0-1.0 s the door ring fills ~0.6 of the frame height and the hall is a compact machine room;
        /// from the 16 m still a ring at 62 m covered only 0.21 H (v1), at 40 m ~0.38 H (Tools/track_camera_model.py).
        /// The drum walls 40-62 m reuse the tunnel module (BendChunks, like the main tunnel) with gold bulb rings every 8.5 m
        /// that continue into the first BuildRings ring at 71.5 m. tunnelStart itself (lead constant) is unchanged.</summary>
        internal const float HallMouthD = 40f;

        static readonly Dictionary<string, Material> hallMats = new Dictionary<string, Material>();

        /// <summary>Lighter, partly self-lit copies of the shared machine materials for the r7 hall set (saved in GenDir):
        /// the reference towers / console / front wall are light lavender-pink and hot pink, while the shared smooth
        /// M_MachineLavender / M_MachinePink reflected the dark drum and rendered navy and plum in the hall (v1 still).</summary>
        static Material HallMat(string src, string name, string hex, float smooth, string emission)
        {
            if (hallMats.TryGetValue(name, out var m) && m != null) return m;
            var s = Mat(src);
            if (s == null) return null;
            m = new Material(s) { name = name };
            if (ColorUtility.TryParseHtmlString(hex, out var c)) m.SetColor("_BaseColor", c);
            m.SetFloat("_Smoothness", smooth);
            if (ColorUtility.TryParseHtmlString(emission, out var e)) { m.EnableKeyword("_EMISSION"); m.SetColor("_EmissionColor", e); }
            AssetDatabase.CreateAsset(m, $"{GenDir}/{name}.mat");
            hallMats[name] = m;
            return m;
        }

        /// <summary>Swaps shared materials by name on one placed r7 object (map: old name -> replacement).</summary>
        static void HallRemap(GameObject go, Dictionary<string, Material> map)
        {
            foreach (var r in go.GetComponentsInChildren<Renderer>())
            {
                var mats = r.sharedMaterials;
                bool changed = false;
                for (int i = 0; i < mats.Length; i++)
                    if (mats[i] != null && map.TryGetValue(mats[i].name, out var rep) && rep != null) { mats[i] = rep; changed = true; }
                if (changed) r.sharedMaterials = mats;
            }
        }

        static void HallWallItem(GameObject holder, float d, int side, string name, float lat, float h, float scale)
        {
            var f = track.Evaluate(d);
            // display (asset -Z) toward the slide, angled 35 deg toward the oncoming player
            var rot = Quaternion.LookRotation(f.flatRight * side, Vector3.up) * Quaternion.Euler(0f, 35f * side, 0f);
            HallPlace(holder, "Machinery", name, f.FlatPoint(lat * side, h), rot, scale);
        }

        static partial void BuildHallExtras(GameObject env, float trackLength)
        {
            // Old hall props that the video does not show: purple pillars, agitator column, spiky rollers, the old console,
            // floating gold pipe segments, valve wheel, porthole (round 7: hidden, replaced by the r7 set below).
            var old = env.transform.Find("HallMachinery");
            if (old != null) old.gameObject.SetActive(false);

            var holder = Child(env, "HallExtras_r7");
            var cam = RearStillCam(16f, 16f / 9f);
            Vector3 P(float u, float v, float depth) => HallScreenPoint(cam, u, v, depth);

            // ---- S1 shot-matched set: reference f_00.50s (1280x720), camera = still 01_hall_start (16 m)
            // pink console, screen centre u 0.11 v 0.22 (body u 0-0.29, v 0.05-0.32), towels on top
            var p = P(0.11f, 0.22f, 8.5f);
            HallPlace(holder, "Machinery", "SM_HallConsole_r7", p, HallFaceCam(cam, p, 22f), 1.5f, new Vector3(0.85f, 1.0f, -0.7f));
            // glowing cyan glass arches behind / above the console
            p = P(0.24f, 0.07f, 12f);
            HallPlace(holder, "Machinery", "SM_CyanPipeArch_r7", p, HallFaceCam(cam, p, 8f), 1.45f);
            // big fluffy roller upper left of the door ring, seen from the side (stripes side by side), hub on the left;
            // >= 2.6 m above the slide so the rear camera and a jumping mascot pass under it
            // r8 v2 (asset artist, owner sheet 01 item 2 "lower placement", proportion fix): reference f_00.50s roller spans
            // u .30-.59 / v 0-.38 of the frame, ours (v1 still) u .22-.45 / v 0-.19 -> 1.3x larger and lower (v .06 -> .14),
            // lifted back only as far as the 2.6 m slide clearance needs (HallRollerClear logs it)
            var rRot = HallRollerRot(cam.rot * new Vector3(-1f, 0.1f, 0.35f));
            p = HallRollerClear(P(0.36f, 0.14f, 9.5f), rRot, 1.5f, 2.6f, "S1");
            HallRoller(holder, p, rRot, 1.5f, 40f);
            // polished gold pipes and valves on the left below the console
            p = P(0.06f, 0.5f, 7.5f);
            HallPlace(holder, "Machinery", "SM_GoldValves_r7", p, HallFaceCam(cam, p, 35f), 1.0f, new Vector3(0f, 1.8f, 0f));
            // lavender tower with the gold paw emblem at the right edge (paw u 0.975 v 0.19)
            p = P(0.975f, 0.19f, 13f);
            HallTower(holder, p, HallFaceCam(cam, p, -12f), 1.2f);

            // ---- tunnel mouth at 40 m: thick gold bulb door ring, lavender machine front wall (two sizes close the hall)
            var fm = track.Evaluate(HallMouthD);
            HallPlace(holder, "Machinery", "SM_MouthRing_r7", fm.FlatPoint(0f, TunnelCenter), fm.FlatRotation, 1.0f);
            var fw = track.Evaluate(HallMouthD + 0.35f);
            HallPlace(holder, "Machinery", "SM_MouthWall_r7", fw.FlatPoint(0f, TunnelCenter), fw.FlatRotation, 0.85f);
            fw = track.Evaluate(HallMouthD + 0.7f);
            HallPlace(holder, "Machinery", "SM_MouthWall_r7", fw.FlatPoint(0f, TunnelCenter), fw.FlatRotation, 1.3f);
            // drum walls 40 -> 62 m (same module as the main tunnel) + gold bulb rings every 8.5 m into BuildRings' 71.5 m
            var tunnel = ModelParts("Track", "SM_Tunnel_Module");
            var tpart = tunnel.Count > 0 ? tunnel[0]
                : new Part(ProceduralModules.TunnelModule(TunnelRadius, TunnelCenter), new[] { Mat("M_DrumWall") }, Matrix4x4.identity);
            BendChunks(holder, "MouthDrum_r7", tpart, HallMouthD + 0.2f, tunnelStart, false, Vector3.one, 0f, 0f, 4f, castShadows: false);
            var ringPrefab = ModelPrefab("Track", "SM_Ring");
            if (ringPrefab != null)
                foreach (float dr in new[] { HallMouthD + 1.0f, HallMouthD + 6f, HallMouthD + 14.5f, HallMouthD + 23f })
                {
                    var frg = track.Evaluate(dr);
                    var rg = Spawn(ringPrefab);
                    rg.name = "MouthDrumRing_r7";
                    rg.transform.SetParent(holder.transform, false);
                    rg.transform.SetPositionAndRotation(frg.FlatPoint(0f, TunnelCenter), frg.FlatRotation);
                }
            // around the door (reference 0.0-2.0 s): towers with paw emblems both sides, console + towels upper left,
            // cyan arches above it, gold valves upper right, a roller hanging upper left in front of the door
            var f = track.Evaluate(HallMouthD - 2.6f);
            HallTower(holder, f.FlatPoint(7.3f, TunnelCenter + 2.2f), f.FlatRotation, 1.25f);
            HallTower(holder, f.FlatPoint(-7.6f, TunnelCenter + 1.6f), f.FlatRotation, 1.25f);
            HallPlace(holder, "Machinery", "SM_HallConsole_r7", f.FlatPoint(-5.0f, 6.6f), f.FlatRotation * Quaternion.Euler(0f, -12f, 0f), 1.4f);
            HallPlace(holder, "Machinery", "SM_CyanPipeArch_r7", track.Evaluate(HallMouthD - 0.5f).FlatPoint(-2.6f, 10.6f), f.FlatRotation, 1.5f);
            HallPlace(holder, "Machinery", "SM_GoldValves_r7", f.FlatPoint(4.8f, 7.2f), f.FlatRotation, 1.15f);
            // Screen S2 pass 2 (asset artist, judge gaps #2 / #4): shot-matched on the S2 comparison camera R2 (mascot at
            // 35 m, CaptureTools "R2_rear_S2_like_3s"). Reference f_03.00s: a big pink fluffy roller fills the upper-left
            // corner (0,0)-(280,160) in FRONT of the hatch rim; left of the rim a dark blue machine housing with a
            // horizontal polished gold pipe + collars at y ~200-235 running into the rim (x 60-245).
            // The door roller (r8 v2: 36 m, 6.2 m high = above the R2 frame) moves to where R2 sees it. Its fur bottom stays
            // >= 2.6 m above the slide level everywhere within 12 m of the centre line (HallRollerClear corridor 12, logged),
            // not only over the 3 m corridor: v2 (5.6 m deep, scale 1.45) was 3.6 m+ to the side but only ~2 m above it.
            // v3: 6.3 m deep + scale 1.6 keeps the corner coverage with the lift; axis closer to the door plane (z .1).
            var r2 = R2Cam();
            // Screen ALL pass 4 (judge gap #4 "thin donut ring seen end-on"): with the axis z +.1 the open non-hub end turned
            // TOWARD the camera (its hollow end read as a donut at x 250-320); z -.2 turns that end away so R2 sees the fur
            // BODY, and u .035 -> 0 keeps the body in the reference corner (0-280 px) instead of the end
            var dRot = HallRollerRot(r2.rot * new Vector3(-1f, 0.1f, -0.2f));
            // v1: the r8 layout showed its blue / white non-hub half here (corner 78 % blue) -> pink-dominant s2 body
            HallRoller(holder, HallRollerClear(HallScreenPoint(r2, 0.0f, -0.08f, 6.3f), dRot, 1.6f, 2.6f, "door/S2", 12f), dRot, 1.6f, -36f,
                       "SM_BrushRoller_s2");
            // blue machine housing + gold pipe (SM_DoorMachine_s2, build_door_machinery_s2.py): front parallel to the door
            // wall, flange end (asset -X) at the rim; centre at R2 (u .06, v .32), 7 m deep = in front of the wall (40.35 m)
            // (v1 u .03 / v .29: pipe at y ~190 and flange at x ~165; reference pipe y 195-235 reaching the rim at x ~245)
            var mp = HallScreenPoint(r2, 0.06f, 0.32f, 7.0f);
            var mach = HallPlace(holder, "Machinery", "SM_DoorMachine_s2", mp, fm.FlatRotation, 1.0f);
            if (mach != null)
            {
                HallOwnMaterials(mach);
                HallLods(mach, "DoorMachine_LOD0", "DoorMachine_LOD1");
                var fmp = track.Evaluate(Mathf.Clamp(HallMouthD - 0.6f, 0f, HallMouthD));
                Debug.Log($"[BWK] hall S2 machinery: centre {mp}, lateral {Vector3.Dot(mp - fmp.position, fmp.flatRight):F2} m, " +
                          $"height over the slide {mp.y - fmp.position.y:F2} m");
            }

            // ---- the hall between start and door (density: no stretch without landmarks; |lateral| >= 4.6 m or high)
            HallWallItem(holder, 26f, 1, "SM_GoldValves_r7", 6.8f, -0.4f, 1.2f);
            HallWallItem(holder, 29f, -1, "SM_HallConsole_r7", 7.4f, 0.6f, 1.3f);
            HallWallItem(holder, 33f, -1, "SM_CyanPipeArch_r7", 8.4f, 4.4f, 1.4f);
            HallWallItem(holder, 33f, 1, "SM_HallConsole_r7", 7.4f, 0.8f, 1.3f);
            var fr2 = track.Evaluate(30f);
            var r2Rot = HallRollerRot(fr2.flatRight + fr2.forward * 0.5f);
            HallRoller(holder, HallRollerClear(fr2.FlatPoint(4.6f, 5.2f), r2Rot, 1.3f, 2.6f, "30m"), r2Rot, 1.3f, 34f);
            foreach (var (d, side) in new[] { (22f, 1), (26f, -1) })
            {
                var ft = track.Evaluate(d);
                HallTower(holder, ft.FlatPoint(9.6f * side, 4.4f), Quaternion.LookRotation(ft.flatRight * side, Vector3.up) * Quaternion.Euler(0f, 30f * side, 0f), 1.2f);
            }

            // r8 v2 (asset artist, asset 01 / sheet 01 item 1): the consoles get their own glossy hot-pink body + deep blue
            // screen (MaterialLibrary.Assets.cs) before the shared hall remap below; the gold / buttons / neon stay as they are
            var consoleMap = new Dictionary<string, Material>
            {
                ["M_MachinePink"] = Mat("M_ConsolePink_r8"),
                ["M_Screen"] = Mat("M_ConsoleScreen_r8"),
            };
            foreach (Transform t in holder.transform)
                if (t.name == "SM_HallConsole_r7") HallRemap(t.gameObject, consoleMap);

            // ---- light lavender-pink / hot pink machine materials for the whole r7 set (not the shared materials)
            var map = new Dictionary<string, Material>
            {
                // round 8 (lighting, owner sheet 01 item 1 "prominent PINK console"): measured S1 upper half f_00.50s pink
                // 22.4 % / blue-purple 33.7 % vs ours 6.3 % / 56.1 %: the light lavender / pink albedos times the saturated
                // blue-violet trilight ambient rendered navy and plum. Matte-er surfaces + stronger warm pink / lilac self-light
                // so the hall pieces keep their own colour under the blue ambient (the tunnel walls are not touched).
                ["M_MachineLavender"] = HallMat("M_MachineLavender", "M_HallLavender_r7", "#F2C6F2", 0.32f, "#A0609C"),
                ["M_MachinePink"] = HallMat("M_MachinePink", "M_HallPink_r7", "#FF5AAE", 0.42f, "#C02A78"),
            };
            HallRemap(holder, map);
            Debug.Log($"[BWK] hall r7: {holder.transform.childCount} props placed, door ring + drum walls from {HallMouthD} m, old HallMachinery hidden");
        }

        static partial void BuildPortalExtras(GameObject env, RunnerController runner)
        {
            var portal = env.transform.Find("LightPortal");
            if (portal == null) { Debug.LogWarning("[BWK] portal r7: LightPortal missing"); return; }
            var pgo = portal.gameObject;
            // the plain glowing disc becomes a small bright core; the flat ray quad is replaced by the 3D starburst
            var core = portal.Find("Core");
            if (core != null) core.localScale = Vector3.one * 0.32f;
            var oldRays = portal.Find("Rays");
            if (oldRays != null) oldRays.gameObject.SetActive(false);

            // golden starburst (rays + sparkle stars) inside the bulb ring, slowly turning in the portal plane
            // r8 v2 (asset artist, asset 24): soft additive SM_Starburst_r8 (many thin fading rays, sparkles, cream core) in
            // the same place / scale; r7 stays the fallback
            string burstName = ModelPrefab("Lighting", "SM_Starburst_r8") != null ? "SM_Starburst_r8" : "SM_Starburst_r7";
            var burst = HallPlace(pgo, "Lighting", burstName, Vector3.zero, Quaternion.identity, 0.55f, default, false);
            if (burst != null)
            {
                burst.transform.localPosition = new Vector3(0f, 0f, 1.3f);
                burst.transform.localRotation = Quaternion.identity;
                var sp = burst.AddComponent<Spinner>();
                sp.localAxis = Vector3.forward;
                sp.degreesPerSecond = 5f;
                // v1 rays read white (M_PortalCore blooms to white); the reference rays are saturated gold
                // round 8 (lighting): M_Neon_Yellow's cream core still bloomed white -> dedicated amber-gold M_PortalBurst
                HallRemap(burst, new Dictionary<string, Material> { ["M_PortalCore"] = Mat("M_PortalBurst") ?? Mat("M_Neon_Yellow") });
            }
            // big polished gold ring with 20 warm bulbs in front of the existing portal ring (reference 13-15 s)
            var ring = HallPlace(pgo, "Machinery", "SM_MouthRing_r7", Vector3.zero, Quaternion.identity, 0.66f, default, false);
            if (ring != null)
            {
                ring.transform.localPosition = new Vector3(0f, 0f, -0.35f);
                ring.transform.localRotation = Quaternion.identity;
            }

            PlacePortalChamber(env);
            Debug.Log("[BWK] portal r7: starburst, bulb ring, chamber window and cyan pipe placed");
        }

        // Screen ALL pass 4 (asset artist, judge gap #2 S7): the chamber stood at portalD - 11 m, 1.3 m BEHIND the finale
        // camera (rest portalD - 5.5, camera back 2.75 + 1.4 => ~portalD - 9.7), so 10_finale showed none of it (crop
        // (0,0,360,510): gold 0.6 % / rainbow 0.3 % vs ref f_14.25s 8.7 / 30.9). Reference: the big porthole fills the
        // screen-left (centre ~x 150, 510 px tall, vfov 57) => centre ~4.7 m ahead of the camera at 3.45 m lateral =
        // portalD - 5.0, still turned 37 deg toward the oncoming camera; the cyan pipe leaves its downstream (portal) side.
        const float PortalChamberBefore = 5.0f;

        /// <summary>S7 rainbow sock chamber on the travel-left wall beside the resting mascot + the cyan pipe curving down
        /// from it (replaces earlier copies; also called by the -bwkEnvChambers preview).</summary>
        static void PlacePortalChamber(GameObject env)
        {
            foreach (var n in new[] { "PortalChamber_r8", "PortalChamber_r7", "PortalCyanPipe_r8", "SM_CyanPipeCurve_r7" })
            {
                var old = env.transform.Find(n);
                if (old != null) Object.DestroyImmediate(old.gameObject);
            }
            var fwin = track.Evaluate(portalD - PortalChamberBefore);
            // r8 masters (asset artist): the master door prefab replaces the v2 window here too (v2 = fallback)
            var door = WashDoorMasterPrefab();
            var win = door != null ? null : ModelPrefab("Machinery", "SM_ChamberWindow_v2");
            if (door != null || win != null)
            {
                var go = door != null ? (GameObject)PrefabUtility.InstantiatePrefab(door) : Spawn(win);
                go.name = door != null ? "PortalChamber_r8" : "PortalChamber_r7";
                go.transform.SetParent(env.transform, false);
                // v2 (preview v1: frame right edge x ~450 overlapped the portal ring's left side, ref edge x ~360):
                // 0.3 m further out + 8 % smaller
                go.transform.SetPositionAndRotation(fwin.FlatPoint(-3.75f, TunnelCenter + 0.2f),
                    Quaternion.LookRotation(Vector3.ProjectOnPlane(fwin.flatRight - fwin.forward * 0.75f, Vector3.up).normalized, Vector3.up));
                go.transform.localScale = Vector3.one * 0.92f;
                foreach (var r in go.GetComponentsInChildren<Renderer>()) r.shadowCastingMode = ShadowCastingMode.Off;
            }
            var fp = track.Evaluate(portalD - PortalChamberBefore + 1.8f);
            var pipe = HallPlace(env, "Machinery", "SM_CyanPipeCurve_r7", fp.FlatPoint(-3.7f, 0.5f), fp.FlatRotation, 1.0f);
            if (pipe != null) pipe.name = "PortalCyanPipe_r8";
        }
    }
}

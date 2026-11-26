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

        /// <summary>Brush roller = spinning bristle body (about its own X axis, like the video) + static gold hub and arm.</summary>
        static void HallRoller(GameObject parent, Vector3 pos, Quaternion rot, float scale, float spin)
        {
            var body = HallPlace(parent, "Machinery", "SM_BrushRoller_r7", pos, rot, scale, default, false);
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
            // pink console, screen centre u 0.11 v 0.21 (body u 0-0.29), towels on top
            var p = P(0.11f, 0.21f, 9.5f);
            HallPlace(holder, "Machinery", "SM_HallConsole_r7", p, HallFaceCam(cam, p, 18f), 1.25f, new Vector3(0.85f, 1.0f, -0.7f));
            // glowing cyan glass arches behind the console (u 0.24-0.37, top cut by the frame)
            p = P(0.31f, 0.11f, 15f);
            HallPlace(holder, "Machinery", "SM_CyanPipeArch_r7", p, HallFaceCam(cam, p, 8f), 1.15f);
            // big fluffy brush roller top centre (u 0.34-0.61, v 0-0.38), gold hub upper left, near end toward the camera
            p = P(0.49f, 0.15f, 8.5f);
            HallRoller(holder, p, HallRollerRot(cam.rot * new Vector3(-1f, 0.12f, 0.75f)), 1.15f, 40f);
            // polished gold pipes and valves on the left below the console (reference gold rails v 0.34-0.5)
            p = P(0.06f, 0.5f, 7.5f);
            HallPlace(holder, "Machinery", "SM_GoldValves_r7", p, HallFaceCam(cam, p, 35f), 1.0f, new Vector3(0f, 1.8f, 0f));
            // lavender tower with the gold paw emblem at the right edge (paw u 0.975 v 0.19)
            p = P(0.975f, 0.19f, 13f);
            HallTower(holder, p, HallFaceCam(cam, p, -12f), 1.2f);

            // ---- tunnel mouth = the washing-machine door: thick gold bulb ring in a lavender machine front wall
            var fm = track.Evaluate(tunnelStart - 0.6f);
            HallPlace(holder, "Machinery", "SM_MouthRing_r7", fm.FlatPoint(0f, TunnelCenter), fm.FlatRotation, 0.9f);
            var fw = track.Evaluate(tunnelStart - 0.25f);
            HallPlace(holder, "Machinery", "SM_MouthWall_r7", fw.FlatPoint(0f, TunnelCenter), fw.FlatRotation, 0.92f);
            // around the mouth (reference 0.0-2.0 s): towers with paw emblems both sides, console + towels upper left,
            // cyan arches above it, gold valves upper right, a roller hanging in front of the mouth on the upper left
            var f = track.Evaluate(tunnelStart - 1.3f);
            HallTower(holder, f.FlatPoint(7.3f, TunnelCenter + 2.2f) - f.forward * 1.1f, f.FlatRotation, 1.25f);
            HallTower(holder, f.FlatPoint(-7.6f, TunnelCenter + 1.6f) - f.forward * 1.1f, f.FlatRotation, 1.25f);
            HallPlace(holder, "Machinery", "SM_HallConsole_r7", f.FlatPoint(-5.0f, 6.4f), f.FlatRotation * Quaternion.Euler(0f, -12f, 0f), 1.4f);
            HallPlace(holder, "Machinery", "SM_CyanPipeArch_r7", track.Evaluate(tunnelStart - 0.9f).FlatPoint(-2.4f, 10.4f), f.FlatRotation, 1.5f);
            HallPlace(holder, "Machinery", "SM_GoldValves_r7", f.FlatPoint(4.6f, 7.0f), f.FlatRotation, 1.15f);
            var fr = track.Evaluate(tunnelStart - 7f);
            HallRoller(holder, fr.FlatPoint(-3.6f, 6.6f), HallRollerRot(-fr.flatRight * 1f + fr.forward * 0.6f), 1.2f, -36f);

            // ---- the hall between (density: no stretch without landmarks; all |lateral| >= 4 m or >= 6 m high)
            var wall = new (float d, int side, string name, float lat, float h, float scale)[]
            {
                (26f, -1, "SM_HallConsole_r7", 7.4f, 0.6f, 1.3f), (31f, 1, "SM_GoldValves_r7", 7.0f, -0.6f, 1.2f),
                (36f, -1, "SM_CyanPipeArch_r7", 8.6f, 4.2f, 1.4f), (41f, 1, "SM_HallConsole_r7", 7.8f, 0.4f, 1.3f),
                (46f, -1, "SM_GoldValves_r7", 7.6f, -0.2f, 1.2f), (50f, 1, "SM_CyanPipeArch_r7", 8.8f, 4.6f, 1.4f),
            };
            foreach (var w in wall)
            {
                var fw2 = track.Evaluate(w.d);
                // display (asset -Z) toward the slide, angled 35 deg toward the oncoming player
                Vector3 inward = -fw2.flatRight * w.side;
                var rot = Quaternion.LookRotation(-inward, Vector3.up) * Quaternion.Euler(0f, 35f * w.side, 0f);
                HallPlace(holder, "Machinery", w.name, fw2.FlatPoint(w.lat * w.side, w.h), rot, w.scale);
            }
            foreach (var (d, lat, h, hubSide) in new[] { (33f, 4.6f, 6.4f, 1f), (44f, -4.8f, 6.8f, -1f) })
            {
                var fr2 = track.Evaluate(d);
                HallRoller(holder, fr2.FlatPoint(lat, h), HallRollerRot(fr2.flatRight * hubSide + fr2.forward * 0.5f), 1.1f, 34f * hubSide);
            }
            foreach (var (d, side) in new[] { (29f, 1), (39f, -1), (54f, 1) })
            {
                var ft = track.Evaluate(d);
                HallTower(holder, ft.FlatPoint(9.6f * side, 4.4f), Quaternion.LookRotation(ft.flatRight * side, Vector3.up) * Quaternion.Euler(0f, 30f * side, 0f), 1.2f);
            }
            Debug.Log($"[BWK] hall r7: {holder.transform.childCount} props placed, old HallMachinery hidden");
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
            var burst = HallPlace(pgo, "Lighting", "SM_Starburst_r7", Vector3.zero, Quaternion.identity, 0.55f, default, false);
            if (burst != null)
            {
                burst.transform.localPosition = new Vector3(0f, 0f, 1.3f);
                burst.transform.localRotation = Quaternion.identity;
                var sp = burst.AddComponent<Spinner>();
                sp.localAxis = Vector3.forward;
                sp.degreesPerSecond = 5f;
            }
            // big polished gold ring with 20 warm bulbs in front of the existing portal ring (reference 13-15 s)
            var ring = HallPlace(pgo, "Machinery", "SM_MouthRing_r7", Vector3.zero, Quaternion.identity, 0.66f, default, false);
            if (ring != null)
            {
                ring.transform.localPosition = new Vector3(0f, 0f, -0.35f);
                ring.transform.localRotation = Quaternion.identity;
            }

            // rainbow sock chamber on the left wall before the portal + the transparent cyan pipe curving down from it
            var fwin = track.Evaluate(portalD - 6.5f);
            var win = ModelPrefab("Machinery", "SM_ChamberWindow_v2");
            if (win != null)
            {
                var go = Spawn(win);
                go.name = "PortalChamber_r7";
                go.transform.SetParent(env.transform, false);
                go.transform.SetPositionAndRotation(fwin.FlatPoint(-3.45f, TunnelCenter + 0.2f),
                    Quaternion.LookRotation(Vector3.ProjectOnPlane(fwin.flatRight, Vector3.up).normalized, Vector3.up));
                foreach (var r in go.GetComponentsInChildren<Renderer>()) r.shadowCastingMode = ShadowCastingMode.Off;
            }
            var fp = track.Evaluate(portalD - 4.6f);
            HallPlace(env, "Machinery", "SM_CyanPipeCurve_r7", fp.FlatPoint(-3.55f, 0.45f), fp.FlatRotation, 0.95f);
            Debug.Log("[BWK] portal r7: starburst, bulb ring, chamber window and cyan pipe placed");
        }
    }
}

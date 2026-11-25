using System.IO;
using System.Linq;
using Unity.Cinemachine;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace BubbleWash.EditorTools
{
    /// <summary>
    /// Renders real Unity stills of the built scene through the gameplay camera rig (rear view) at fixed track
    /// positions, in landscape 16:9 (for comparison with the reference frames) and portrait 9:16 (mobile), plus
    /// front-facing comparison angles that match the reference camera in the tunnel section.
    /// Output: Captures/stills/*.png. Batch entry: BubbleWash.EditorTools.CaptureTools.CaptureStillsBatch
    /// </summary>
    public static class CaptureTools
    {
        public const string OutDir = "Captures/stills";

        public static void CaptureStillsBatch()
        {
            try { CaptureStills(); EditorApplication.Exit(0); }
            catch (System.Exception e) { Debug.LogError("[BWK] capture failed: " + e); EditorApplication.Exit(1); }
        }

        [MenuItem("Bubble Wash/Capture Stills")]
        public static void CaptureStills()
        {
            if (EditorSceneManager.GetActiveScene().path != SceneBuilder.ScenePath)
                EditorSceneManager.OpenScene(SceneBuilder.ScenePath);
            Directory.CreateDirectory(OutDir);
            var runner = Object.FindFirstObjectByType<RunnerController>();
            var rig = Object.FindFirstObjectByType<RunnerCameraRig>(FindObjectsInactive.Include);
            var cam = Camera.main;
            if (runner == null || rig == null || cam == null) { Debug.LogError("[BWK] capture: scene objects missing"); return; }
            var brain = cam.GetComponent<CinemachineBrain>();
            if (brain) brain.enabled = false;
            runner.track.Rebuild();
            float L = runner.track.Length;

            var animator = runner.GetComponentInChildren<Animator>();
            AnimationClip slide = null;
            if (animator != null && animator.runtimeAnimatorController != null)
                slide = animator.runtimeAnimatorController.animationClips.FirstOrDefault(c => c.name == "Slide");

            foreach (var ps in Object.FindObjectsByType<ParticleSystem>(FindObjectsSortMode.None))
                if (ps.name == "AmbientBubbles") ps.Simulate(4f, true, true);

            var shots = new (string name, float d, float lat)[]
            {
                ("01_hall_start", 16f, 0f), ("02_hall_curve", 36f, 0f), ("03_tunnel_entry", 55f, 0f),
                ("04_tunnel", 92f, 0f), ("05_tunnel_lane_left", 128f, -1.15f), ("06_tunnel_lane_right", 170f, 1.15f),
                ("07_chambers", 215f, 0f), ("08_sweep", 250f, 0f), ("09_portal", L - 34f, 0f),
            };
            foreach (var s in shots)
            {
                runner.TeleportTo(s.d, s.lat);
                if (slide != null) slide.SampleAnimation(animator.gameObject, 0.25f);
                foreach (var (w, h, tag) in new[] { (1280, 720, "16x9"), (720, 1280, "9x16") })
                {
                    rig.aspectOverride = w / (float)h;
                    rig.Snap();
                    var lens = rig.vcam.Lens;
                    cam.transform.SetPositionAndRotation(rig.transform.position, rig.transform.rotation * Quaternion.Euler(0f, 0f, lens.Dutch));
                    cam.fieldOfView = lens.FieldOfView;
                    Render(cam, w, h, $"{OutDir}/{s.name}_{tag}.png");
                }
            }

            // Front-facing comparison angles (reference 3.75-15 s camera) - comparison only, never used in gameplay.
            foreach (var (name, d) in new[] { ("C1_front_tunnel_like_5s", 100f), ("C2_front_chambers_like_10s", 220f), ("C3_front_portal_like_14s", L - 22f) })
            {
                runner.TeleportTo(d, 0f);
                if (slide != null) slide.SampleAnimation(animator.gameObject, 0.25f);
                var f = runner.Frame;
                Vector3 camPos = runner.transform.position + f.forward * 2.6f + f.flatUp * 0.95f;
                cam.transform.SetPositionAndRotation(camPos, Quaternion.LookRotation(runner.transform.position + f.flatUp * 0.55f - camPos, f.flatUp));
                cam.fieldOfView = 46f;
                Render(cam, 1280, 720, $"{OutDir}/{name}_16x9.png");
            }
            rig.aspectOverride = 0f;
            if (brain) brain.enabled = true;
            Debug.Log("[BWK] Stills written to " + Path.GetFullPath(OutDir));
        }

        public static void Render(Camera cam, int w, int h, string path)
        {
            var rt = RenderTexture.GetTemporary(w, h, 24, RenderTextureFormat.ARGB32, RenderTextureReadWrite.sRGB, 4);
            cam.aspect = w / (float)h;
            CaptureUtil.Render(cam, rt);
            var tex = CaptureUtil.ReadBack(rt, null, TextureFormat.RGB24);
            File.WriteAllBytes(path, tex.EncodeToPNG());
            Object.DestroyImmediate(tex);
            cam.ResetAspect();
            RenderTexture.ReleaseTemporary(rt);
        }
    }
}

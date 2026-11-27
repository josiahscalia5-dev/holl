using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.Animations;
using UnityEngine;

namespace BubbleWash.EditorTools
{
    /// <summary>
    /// Builds the mascot Animator Controller from the clips inside SK_Mascot.fbx:
    /// Idle -> Ride (2D blend: Steer x Curve over Slide/LeanLeft/LeanRight/TurnLeft/TurnRight) <-> Accelerate,
    /// Any -> Jump -> Splash, Any -> Bump, Any -> Celebrate.
    /// </summary>
    public static class AnimatorBuilder
    {
        // OWNER 2026-11-26 21:15 / 21:25: TEST the v4 mascot in-game (pale hat band, raised arms, rounder fluffy body; same
        // 17 bones, 13 takes, 11 material names) and keep the previous model + all animations as the fallback: set
        // UseMascotV4 = false and run a full build to go back to SK_Mascot.fbx (v3). Never delete either FBX.
        public const bool UseMascotV4 = true;
        // Lead 2026-11-27 06:45 (owner 06:20 / 06:30): SK_Mascot_v5.fbx = the character artist's reconstruction of the
        // ORIGINAL approved character, a SEPARATE version. v4 (and v3) stay the complete fallbacks - never deleted, their
        // materials untouched (v5 uses its own *_v5 materials via ModelImportRules.RemapVersionedMaterials). v5 is a correct
        // export (no BWK_RIG_TEST_YAW) -> ModelYaw 0. true + full build = show v5 to the owner in gameplay (NOT an approval:
        // the owner decides); false + full build = v4 exactly as before.
        // Lead cd16e551 2026-11-27 07:40: ON for the owner's requested "V5 inside actual Unity gameplay" previews and for the
        // motion specialist (E) to tune the seated motion on v5. TEST version only - v4 (SK_Mascot_v4.fbx + its materials)
        // stays untouched; set false + full build to return to v4 exactly.
        public const bool UseMascotV5 = true;
        public const string FbxPathV3 = "Assets/BubbleWashKingdom/Art/Models/Characters/SK_Mascot.fbx";
        public const string FbxPathV4 = "Assets/BubbleWashKingdom/Art/Models/Characters/SK_Mascot_v4.fbx";
        public const string FbxPathV5 = "Assets/BubbleWashKingdom/Art/Models/Characters/SK_Mascot_v5.fbx";
        public const string FbxPath = UseMascotV5 ? FbxPathV5 : UseMascotV4 ? FbxPathV4 : FbxPathV3;
        // Lead 2026-11-26 21:40: SK_Mascot_v4.fbx was exported with the TEST-ONLY BWK_RIG_TEST_YAW=180 of
        // build_mascot_rig.py (its Armature object has yaw -180 in Blender, SK_Mascot.fbx has 0), so in-game the rear camera
        // saw its face while sliding and its back in the celebration (s2p3 recording). SceneBuilder turns the model root by
        // this yaw so v4 faces the travel direction like v3. A re-export without the test yaw must set this back to 0.
        public const float ModelYaw = UseMascotV5 ? 0f : UseMascotV4 ? 180f : 0f;
        public const string ControllerPath = "Assets/BubbleWashKingdom/Animation/Mascot.controller";
        // Motion E 2026-11-27 pass 9 (owner 10:48 / 12:08, reference 01 + crop 23b): the Ride centre "Slide" = the FBX take with
        // the seated arms raised UP-OUTWARD beside the brim baked in (BubbleWash.SeatedArmSolver: collision-checked against the
        // knitted cuff), so the hero stills (they sample "Slide"), the Ride blend and the arm hold all show the same pose.
        // The FBX and its takes stay untouched. false + full build = the FBX's own Slide take exactly as before.
        public const bool BakeSeatedSlide = true;
        public const string SeatedSlidePath = "Assets/BubbleWashKingdom/Animation/SeatedSlide/Slide.anim";

        [MenuItem("Bubble Wash/Setup/4 Build Animator")]
        public static RuntimeAnimatorController Run()
        {
            Directory.CreateDirectory(Path.GetDirectoryName(ControllerPath));
            var clips = AssetDatabase.LoadAllAssetsAtPath(FbxPath).OfType<AnimationClip>()
                .Where(c => !c.name.StartsWith("__preview__"))
                .GroupBy(c => c.name).ToDictionary(g => g.Key, g => g.First());
            Debug.Log($"[BWK] Mascot clips found: {string.Join(", ", clips.Keys)}");
            if (BakeSeatedSlide && clips.TryGetValue("Slide", out var fbxSlide))
            {
                var seated = BakeSeatedSlideAsset(fbxSlide);
                if (seated != null) clips["Slide"] = seated;
            }

            AnimationClip Clip(params string[] names)
            {
                foreach (var n in names) if (clips.TryGetValue(n, out var c)) return c;
                return null;
            }

            if (File.Exists(ControllerPath)) AssetDatabase.DeleteAsset(ControllerPath);
            var ctrl = AnimatorController.CreateAnimatorControllerAtPath(ControllerPath);
            ctrl.AddParameter("Steer", AnimatorControllerParameterType.Float);
            ctrl.AddParameter("Curve", AnimatorControllerParameterType.Float);
            ctrl.AddParameter("Speed", AnimatorControllerParameterType.Float);
            ctrl.AddParameter(new AnimatorControllerParameter { name = "Grounded", type = AnimatorControllerParameterType.Bool, defaultBool = true });
            ctrl.AddParameter("Boost", AnimatorControllerParameterType.Bool);
            ctrl.AddParameter("Running", AnimatorControllerParameterType.Bool);
            ctrl.AddParameter("Jump", AnimatorControllerParameterType.Trigger);
            ctrl.AddParameter("Land", AnimatorControllerParameterType.Trigger);
            ctrl.AddParameter("Bump", AnimatorControllerParameterType.Trigger);
            ctrl.AddParameter("Celebrate", AnimatorControllerParameterType.Trigger);

            var sm = ctrl.layers[0].stateMachine;
            var slide = Clip("Slide", "Idle");

            var idle = sm.AddState("Idle", new Vector3(250, 0));
            idle.motion = Clip("Idle", "Slide");

            var ride = ctrl.CreateBlendTreeInController("Ride", out BlendTree tree, 0);
            tree.blendType = BlendTreeType.FreeformDirectional2D;
            tree.blendParameter = "Steer";
            tree.blendParameterY = "Curve";
            tree.useAutomaticThresholds = false;
            AddChild(tree, slide, Vector2.zero);
            AddChild(tree, Clip("LeanLeft"), new Vector2(-1f, 0f));
            AddChild(tree, Clip("LeanRight"), new Vector2(1f, 0f));
            AddChild(tree, Clip("TurnLeft", "LeanLeft"), new Vector2(0f, -1f));
            AddChild(tree, Clip("TurnRight", "LeanRight"), new Vector2(0f, 1f));

            var accel = sm.AddState("Accelerate", new Vector3(500, 120));
            accel.motion = Clip("Accelerate", "Slide");
            var jump = sm.AddState("Jump", new Vector3(500, -120));
            jump.motion = Clip("Jump");
            var splash = sm.AddState("Splash", new Vector3(750, -120));
            splash.motion = Clip("Splash", "Slide");
            var bump = sm.AddState("Bump", new Vector3(750, 0));
            bump.motion = Clip("Bump", "Balance", "Slide");
            var celebrate = sm.AddState("Celebrate", new Vector3(750, 240));
            celebrate.motion = Clip("Celebrate", "Idle");
            sm.defaultState = idle;

            var t = idle.AddTransition(ride); t.hasExitTime = false; t.duration = 0.25f;
            t.AddCondition(AnimatorConditionMode.If, 0, "Running");
            t = ride.AddTransition(idle); t.hasExitTime = false; t.duration = 0.3f;
            t.AddCondition(AnimatorConditionMode.IfNot, 0, "Running");
            t = ride.AddTransition(accel); t.hasExitTime = false; t.duration = 0.2f;
            t.AddCondition(AnimatorConditionMode.If, 0, "Boost");
            t = accel.AddTransition(ride); t.hasExitTime = false; t.duration = 0.3f;
            t.AddCondition(AnimatorConditionMode.IfNot, 0, "Boost");

            var aj = sm.AddAnyStateTransition(jump); aj.hasExitTime = false; aj.duration = 0.08f; aj.canTransitionToSelf = false;
            aj.AddCondition(AnimatorConditionMode.If, 0, "Jump");
            t = jump.AddTransition(splash); t.hasExitTime = false; t.duration = 0.06f;
            t.AddCondition(AnimatorConditionMode.If, 0, "Land");
            t = jump.AddTransition(ride); t.hasExitTime = true; t.exitTime = 1f; t.duration = 0.15f;
            t.AddCondition(AnimatorConditionMode.If, 0, "Grounded");
            t = splash.AddTransition(ride); t.hasExitTime = true; t.exitTime = 0.85f; t.duration = 0.15f;

            var ab = sm.AddAnyStateTransition(bump); ab.hasExitTime = false; ab.duration = 0.05f; ab.canTransitionToSelf = false;
            ab.AddCondition(AnimatorConditionMode.If, 0, "Bump");
            t = bump.AddTransition(ride); t.hasExitTime = true; t.exitTime = 0.9f; t.duration = 0.2f;

            var ac = sm.AddAnyStateTransition(celebrate); ac.hasExitTime = false; ac.duration = 0.3f; ac.canTransitionToSelf = false;
            ac.AddCondition(AnimatorConditionMode.If, 0, "Celebrate");
            t = celebrate.AddTransition(idle); t.hasExitTime = false; t.duration = 0.3f;
            t.AddCondition(AnimatorConditionMode.If, 0, "Running");

            AssetDatabase.SaveAssets();
            Debug.Log("[BWK] Animator built: " + ControllerPath);
            return ctrl;
        }

        static void AddChild(BlendTree tree, Motion m, Vector2 pos)
        {
            if (m != null) tree.AddChild(m, pos);
        }

        /// <summary>Bakes the seated "Slide" from the FBX take on a temporary model instance and saves it (SeatedSlidePath).
        /// Any failure keeps the FBX's own Slide take.</summary>
        static AnimationClip BakeSeatedSlideAsset(AnimationClip src)
        {
            GameObject inst = null;
            try
            {
                var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(FbxPath);
                if (prefab == null) return null;
                inst = Object.Instantiate(prefab);
                inst.hideFlags = HideFlags.HideAndDontSave;
                var baked = BakeSeatedSlideClip(src, inst, new SeatedArmSettings());
                if (baked == null) return null;
                Directory.CreateDirectory(Path.GetDirectoryName(SeatedSlidePath));
                if (File.Exists(SeatedSlidePath)) AssetDatabase.DeleteAsset(SeatedSlidePath);
                AssetDatabase.CreateAsset(baked, SeatedSlidePath);
                var saved = AssetDatabase.LoadAssetAtPath<AnimationClip>(SeatedSlidePath);
                Debug.Log("[BWK motion] seated Slide baked: " + SeatedSlidePath);
                return saved;
            }
            catch (System.Exception e)
            {
                Debug.LogWarning("[BWK motion] seated Slide bake failed - the FBX Slide take is kept: " + e.Message);
                return null;
            }
            finally { if (inst != null) Object.DestroyImmediate(inst); }
        }

        /// <summary>
        /// Copy of <paramref name="src"/> whose arm / hand curves carry the seated up-outward arms (SeatedArmSolver applied
        /// after sampling the take at 30 keys/s; the shoulder keys only move if the solver needs its outward slide). All
        /// other curves are copied unchanged. <paramref name="go"/> = the GameObject the clip animates (the model root).
        /// </summary>
        public static AnimationClip BakeSeatedSlideClip(AnimationClip src, GameObject go, SeatedArmSettings set)
        {
            var solver = SeatedArmSolver.Create(go.transform);
            if (solver == null) { Debug.LogWarning("[BWK motion] seated Slide: bones / cuff not found - not baked"); return null; }
            var all = go.GetComponentsInChildren<Transform>(true);
            Transform Find(string n) => all.FirstOrDefault(t => t.name == n);
            var bones = new[] { Find("arm.L"), Find("hand.L"), Find("arm.R"), Find("hand.R") };
            var paths = bones.Select(b => AnimationUtility.CalculateTransformPath(b, go.transform)).ToArray();
            var clip = new AnimationClip { name = src.name, frameRate = src.frameRate };
            foreach (var b in AnimationUtility.GetCurveBindings(src))
            {
                int bi = System.Array.IndexOf(paths, b.path);
                bool rot = b.propertyName.StartsWith("m_LocalRotation") || b.propertyName.StartsWith("localEulerAngles");
                bool shoulderPos = b.propertyName.StartsWith("m_LocalPosition") && (bi == 0 || bi == 2);
                if (bi >= 0 && b.type == typeof(Transform) && (rot || shoulderPos)) continue;
                AnimationUtility.SetEditorCurve(clip, b, AnimationUtility.GetEditorCurve(src, b));
            }
            int n = Mathf.Max(12, Mathf.RoundToInt(src.length * 30f));
            var rk = new List<Keyframe>[4, 4];
            var pk = new List<Keyframe>[2, 3];
            for (int i = 0; i < 4; i++) for (int c = 0; c < 4; c++) rk[i, c] = new List<Keyframe>();
            for (int i = 0; i < 2; i++) for (int c = 0; c < 3; c++) pk[i, c] = new List<Keyframe>();
            var prev = new Quaternion[4];
            string at025 = "";
            for (int k = 0; k <= n; k++)
            {
                float t = src.length * k / n;
                src.SampleAnimation(go, t);
                solver.Apply(1f, set, (float)k / n);
                if (at025.Length == 0 && t >= 0.25f) at025 = $"t {t:F2}: " + solver.LastSolve();
                for (int i = 0; i < 4; i++)
                {
                    Quaternion q = bones[i].localRotation;
                    if (k > 0 && Quaternion.Dot(prev[i], q) < 0f) q = new Quaternion(-q.x, -q.y, -q.z, -q.w);
                    prev[i] = q;
                    rk[i, 0].Add(new Keyframe(t, q.x)); rk[i, 1].Add(new Keyframe(t, q.y));
                    rk[i, 2].Add(new Keyframe(t, q.z)); rk[i, 3].Add(new Keyframe(t, q.w));
                }
                for (int i = 0; i < 2; i++)
                {
                    Vector3 p = bones[i * 2].localPosition;
                    pk[i, 0].Add(new Keyframe(t, p.x)); pk[i, 1].Add(new Keyframe(t, p.y)); pk[i, 2].Add(new Keyframe(t, p.z));
                }
            }
            AnimationCurve Smooth(List<Keyframe> keys)
            {
                var cv = new AnimationCurve(keys.ToArray());
                for (int i = 0; i < cv.length; i++) cv.SmoothTangents(i, 0f);
                return cv;
            }
            string[] rc = { "m_LocalRotation.x", "m_LocalRotation.y", "m_LocalRotation.z", "m_LocalRotation.w" };
            string[] pc = { "m_LocalPosition.x", "m_LocalPosition.y", "m_LocalPosition.z" };
            for (int i = 0; i < 4; i++)
                for (int c = 0; c < 4; c++)
                    AnimationUtility.SetEditorCurve(clip, EditorCurveBinding.FloatCurve(paths[i], typeof(Transform), rc[c]), Smooth(rk[i, c]));
            for (int i = 0; i < 2; i++)
                for (int c = 0; c < 3; c++)
                    AnimationUtility.SetEditorCurve(clip, EditorCurveBinding.FloatCurve(paths[i * 2], typeof(Transform), pc[c]), Smooth(pk[i, c]));
            AnimationUtility.SetAnimationClipSettings(clip, AnimationUtility.GetAnimationClipSettings(src));
            clip.EnsureQuaternionContinuity();
            src.SampleAnimation(go, 0.25f);
            Debug.Log($"[BWK motion] seated Slide: {solver.Describe()}; {at025}");
            return clip;
        }

        /// <summary>
        /// Motion E preview (no scene save): CaptureTools.AgentPreviewBatch plus the seated "Slide" bake applied in memory
        /// (AnimatorOverrideController on the scene mascot), so the hero stills show the arms the next full build bakes.
        /// Run: Tools/unity_run.sh BubbleWash.EditorTools.AnimatorBuilder.MotionPreviewBatch LOG -bwkOut DIR [-bwkStills]
        /// </summary>
        public static void MotionPreviewBatch()
        {
            try
            {
                var args = System.Environment.GetCommandLineArgs();
                int oi = System.Array.IndexOf(args, "-bwkOut");
                string outDir = oi >= 0 && oi < args.Length - 1 ? args[oi + 1] : "Captures/agents/motion/preview";
                TextureGenerator.Run();
                MaterialLibrary.Run();
                UnityEditor.SceneManagement.EditorSceneManager.OpenScene(SceneBuilder.ScenePath);
                SceneBuilder.PreviewRefreshDomains();
                var runner = Object.FindFirstObjectByType<RunnerController>();
                var animator = runner != null ? runner.GetComponentInChildren<Animator>() : null;
                var ctrl = animator != null ? animator.runtimeAnimatorController : null;
                var src = ctrl != null ? ctrl.animationClips.FirstOrDefault(c => c != null && c.name == "Slide") : null;
                if (src != null)
                {
                    var baked = BakeSeatedSlideClip(src, animator.gameObject, new SeatedArmSettings());
                    if (baked != null)
                    {
                        var ov = new AnimatorOverrideController(ctrl) { name = "Mascot_SeatedPreview" };
                        ov[src] = baked;
                        animator.runtimeAnimatorController = ov;
                        var seen = ov.animationClips.FirstOrDefault(c => c != null && c.name == "Slide");
                        Debug.Log("[BWK motion] preview: seated Slide override " + (seen == baked ? "ACTIVE" : "NOT seen by the name lookup"));
                    }
                }
                else Debug.LogWarning("[BWK motion] preview: no Slide clip on the scene mascot - stills unchanged");
                CaptureTools.CaptureHero(outDir, outDir);
                if (System.Array.IndexOf(args, "-bwkStills") >= 0) CaptureTools.CaptureStills(outDir + "/stills");
                EditorApplication.Exit(0);
            }
            catch (System.Exception e) { Debug.LogError("[BWK motion] preview failed: " + e); EditorApplication.Exit(1); }
        }
    }
}

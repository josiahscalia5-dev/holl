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
        // OWNER 2026-11-26 21:20 approved the v4 mascot in-game (pale hat band, raised arms, rounder fluffy body; same 17
        // bones, 13 takes, 11 material names as SK_Mascot.fbx, which stays as the fallback). Was SK_Mascot.fbx.
        public const string FbxPath = "Assets/BubbleWashKingdom/Art/Models/Characters/SK_Mascot_v4.fbx";
        public const string ControllerPath = "Assets/BubbleWashKingdom/Animation/Mascot.controller";

        [MenuItem("Bubble Wash/Setup/4 Build Animator")]
        public static RuntimeAnimatorController Run()
        {
            Directory.CreateDirectory(Path.GetDirectoryName(ControllerPath));
            var clips = AssetDatabase.LoadAllAssetsAtPath(FbxPath).OfType<AnimationClip>()
                .Where(c => !c.name.StartsWith("__preview__"))
                .GroupBy(c => c.name).ToDictionary(g => g.Key, g => g.First());
            Debug.Log($"[BWK] Mascot clips found: {string.Join(", ", clips.Keys)}");

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
    }
}

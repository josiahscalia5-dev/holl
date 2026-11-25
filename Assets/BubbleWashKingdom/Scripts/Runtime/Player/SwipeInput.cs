using System;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.EnhancedTouch;
using ETouch = UnityEngine.InputSystem.EnhancedTouch.Touch;
using ETouchPhase = UnityEngine.InputSystem.TouchPhase;

namespace BubbleWash
{
    public enum SwipeDir { Left, Right, Up, Down }

    /// <summary>
    /// Mobile swipe controls (Input System EnhancedTouch) with mouse-drag and keyboard fallbacks for the editor.
    /// A swipe fires as soon as the finger crosses the distance threshold, not on release, so steering feels instant.
    /// </summary>
    public class SwipeInput : MonoBehaviour
    {
        [Tooltip("Swipe distance threshold as a fraction of the screen's shorter side.")]
        public float thresholdFraction = 0.055f;
        [Tooltip("A swipe must cross the threshold within this many seconds.")]
        public float maxSwipeTime = 0.5f;

        public event Action<SwipeDir> Swiped;

        Vector2 startPos;
        double startTime;
        bool tracking;
        bool fired;

        void OnEnable() { EnhancedTouchSupport.Enable(); }

        void Update()
        {
            var kb = Keyboard.current;
            if (kb != null)
            {
                if (kb.leftArrowKey.wasPressedThisFrame || kb.aKey.wasPressedThisFrame) Fire(SwipeDir.Left);
                if (kb.rightArrowKey.wasPressedThisFrame || kb.dKey.wasPressedThisFrame) Fire(SwipeDir.Right);
                if (kb.upArrowKey.wasPressedThisFrame || kb.wKey.wasPressedThisFrame || kb.spaceKey.wasPressedThisFrame) Fire(SwipeDir.Up);
                if (kb.downArrowKey.wasPressedThisFrame || kb.sKey.wasPressedThisFrame) Fire(SwipeDir.Down);
            }

            if (ETouch.activeTouches.Count > 0)
            {
                var t = ETouch.activeTouches[0];
                switch (t.phase)
                {
                    case ETouchPhase.Began: Begin(t.screenPosition, Time.realtimeSinceStartupAsDouble); break;
                    case ETouchPhase.Moved:
                    case ETouchPhase.Stationary: Track(t.screenPosition, Time.realtimeSinceStartupAsDouble); break;
                    default: tracking = false; break;
                }
                return;
            }

            var mouse = Mouse.current;
            if (mouse != null)
            {
                if (mouse.leftButton.wasPressedThisFrame) Begin(mouse.position.ReadValue(), Time.realtimeSinceStartupAsDouble);
                else if (mouse.leftButton.isPressed) Track(mouse.position.ReadValue(), Time.realtimeSinceStartupAsDouble);
                else tracking = false;
            }
        }

        void Begin(Vector2 pos, double time)
        {
            startPos = pos;
            startTime = time;
            tracking = true;
            fired = false;
        }

        void Track(Vector2 pos, double time)
        {
            if (!tracking || fired) return;
            if (time - startTime > maxSwipeTime) { Begin(pos, time); return; }
            Vector2 delta = pos - startPos;
            float threshold = Mathf.Min(Screen.width, Screen.height) * thresholdFraction;
            if (delta.magnitude < threshold) return;
            fired = true;
            if (Mathf.Abs(delta.x) > Mathf.Abs(delta.y)) Fire(delta.x < 0 ? SwipeDir.Left : SwipeDir.Right);
            else Fire(delta.y > 0 ? SwipeDir.Up : SwipeDir.Down);
        }

        public void Fire(SwipeDir dir) => Swiped?.Invoke(dir);
    }
}

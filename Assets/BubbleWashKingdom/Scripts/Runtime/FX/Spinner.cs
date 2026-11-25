using UnityEngine;

namespace BubbleWash
{
    /// <summary>Continuously rotates a transform around a local axis (rollers, agitators, drum interiors).</summary>
    public class Spinner : MonoBehaviour
    {
        public Vector3 localAxis = Vector3.up;
        public float degreesPerSecond = 90f;
        public float wobble = 0f;
        public float wobbleFrequency = 0.5f;
        Quaternion baseRot;
        float phase;

        void Awake() { baseRot = transform.localRotation; phase = Random.value * 10f; }

        void Update()
        {
            float t = Time.time + phase;
            float angle = degreesPerSecond * t + Mathf.Sin(t * wobbleFrequency * Mathf.PI * 2f) * wobble;
            transform.localRotation = baseRot * Quaternion.AngleAxis(angle, localAxis.normalized);
        }
    }
}

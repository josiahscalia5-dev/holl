using UnityEngine;

namespace BubbleWash
{
    /// <summary>Gentle floating motion for laundry in the swirling side chambers.</summary>
    public class FloatBob : MonoBehaviour
    {
        public float amplitude = 0.12f;
        public float frequency = 0.35f;
        public float swayDegrees = 18f;
        public Vector3 orbitAxis = Vector3.forward;
        public float orbitRadius = 0f;
        public float orbitSpeed = 40f;
        Vector3 basePos;
        Quaternion baseRot;
        float phase;

        void Awake() { basePos = transform.localPosition; baseRot = transform.localRotation; phase = Random.value * 10f; }

        void Update()
        {
            float t = Time.time + phase;
            Vector3 orbit = Vector3.zero;
            if (orbitRadius > 0f)
            {
                Quaternion q = Quaternion.AngleAxis(t * orbitSpeed, orbitAxis);
                orbit = q * (Vector3.right * orbitRadius);
            }
            transform.localPosition = basePos + orbit + Vector3.up * Mathf.Sin(t * frequency * Mathf.PI * 2f) * amplitude;
            transform.localRotation = baseRot * Quaternion.Euler(Mathf.Sin(t * 0.7f) * swayDegrees, t * 25f, Mathf.Cos(t * 0.5f) * swayDegrees);
        }
    }
}

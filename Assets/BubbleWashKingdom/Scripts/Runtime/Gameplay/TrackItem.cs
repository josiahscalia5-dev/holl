using System.Collections.Generic;
using UnityEngine;

namespace BubbleWash
{
    public enum TrackItemKind { Coin, Gem, Boost, Obstacle }

    /// <summary>A collectible, boost pad or obstacle placed at (distance, lateral, height) on the track.</summary>
    public class TrackItem : MonoBehaviour
    {
        public TrackItemKind kind;
        public float distance;
        public float lateral;
        public float height = 0.55f;
        [Tooltip("Half extent along the track (m) used for hit tests.")]
        public float halfLength = 0.6f;
        [Tooltip("Half width across the track (m) used for hit tests.")]
        public float halfWidth = 0.6f;
        public bool jumpable = true;
        [Tooltip("Runner height (m) needed to clear a jumpable obstacle.")]
        public float clearHeight = 0.55f;
        public int value = 1;

        [Header("Idle animation")]
        public float spinSpeed = 140f;
        public float bobAmplitude = 0.06f;
        public float bobFrequency = 1.6f;

        public bool Consumed { get; private set; }

        Vector3 basePos;
        Quaternion baseRot;
        float collectT = -1f;
        Vector3 baseScale;
        Transform flyTarget;

        void Awake()
        {
            basePos = transform.localPosition;
            baseRot = transform.localRotation;
            baseScale = transform.localScale;
        }

        public void ResetItem()
        {
            Consumed = false;
            collectT = -1f;
            transform.localPosition = basePos;
            transform.localRotation = baseRot;
            transform.localScale = baseScale;
            gameObject.SetActive(true);
        }

        public void Consume(Transform target)
        {
            if (Consumed) return;
            Consumed = true;
            if (kind == TrackItemKind.Coin || kind == TrackItemKind.Gem)
            {
                collectT = 0f;
                flyTarget = target;
            }
        }

        void Update()
        {
            float t = Time.time;
            if (collectT >= 0f)
            {
                collectT += Time.deltaTime / 0.28f;
                if (flyTarget != null)
                    transform.position = Vector3.Lerp(transform.position, flyTarget.position + flyTarget.up * 0.6f, Mathf.Clamp01(collectT));
                transform.localScale = baseScale * Mathf.Lerp(1.15f, 0.05f, Mathf.Clamp01(collectT));
                if (collectT >= 1f) gameObject.SetActive(false);
                return;
            }
            if (kind == TrackItemKind.Coin || kind == TrackItemKind.Gem)
            {
                transform.localRotation = baseRot * Quaternion.Euler(0f, spinSpeed * t + distance * 7f, 0f);
                float bob = Mathf.Sin(t * bobFrequency * Mathf.PI * 2f + distance) * bobAmplitude;
                transform.localPosition = basePos + (baseRot * Vector3.up) * bob;
            }
        }
    }
}

using UnityEngine;

namespace BubbleWash
{
    /// <summary>
    /// Feeds the mascot Animator from the runner (steer, curve, speed, boost, jump/land/bump/finish) and adds
    /// procedural secondary motion: pom-pom spring lag and squash-and-stretch on jumps and landings, so body,
    /// arms, feet and head move together.
    /// </summary>
    [DefaultExecutionOrder(50)]
    public class MascotAnimatorDriver : MonoBehaviour
    {
        public RunnerController runner;
        public Animator animator;
        [Tooltip("Optional bones found by name if left empty.")]
        public Transform pomPom;
        public Transform squashRoot;

        public float pomStiffness = 60f;
        public float pomDamping = 7f;
        public float pomMaxAngle = 35f;

        // Motion E 2026-11-27 pass 7 (owner 09:20 s8: he SITS UPRIGHT ON HIS BOTTOM, natural arm / foot motion, reacts to jumps
        // and lanes and returns smoothly to the seated pose). The v5 takes Lean / Turn / Balance / Jump / Bump drop the arms
        // 39-50 deg (the rig's cuff solve) while Slide keeps them raised beside the brim, so every curve, lane change, jump
        // and landing made the arms hang. Visual only: after the Animator, the arm / hand bones are blended back toward the
        // Slide take's own pose (sampled once from the clip, phase-matched to the ride blend), keeping part of each
        // reaction's motion. Weight 0 outside running (intro wait, finish turn, celebration keep their clips untouched).
        [Header("Seated arm hold (visual only)")]
        [Range(0f, 1f)] public float armHoldRide = 0.7f;
        [Range(0f, 1f)] public float armHoldAction = 0.55f;
        public string armHoldClip = "Slide";

        // Gentle bounce on the water while seated (visual only, model root; off in the air and after the finish).
        [Header("Water bob (visual only)")]
        public float bobAmplitude = 0.016f;
        public float bobFrequency = 1.7f;
        public float bobRollDeg = 1.1f;
        public float bobPitchDeg = 0.8f;

        static readonly int SteerId = Animator.StringToHash("Steer");
        static readonly int CurveId = Animator.StringToHash("Curve");
        static readonly int SpeedId = Animator.StringToHash("Speed");
        static readonly int GroundedId = Animator.StringToHash("Grounded");
        static readonly int BoostId = Animator.StringToHash("Boost");
        static readonly int RunningId = Animator.StringToHash("Running");
        static readonly int JumpId = Animator.StringToHash("Jump");
        static readonly int LandId = Animator.StringToHash("Land");
        static readonly int BumpId = Animator.StringToHash("Bump");
        static readonly int CelebrateId = Animator.StringToHash("Celebrate");

        Vector3 pomAngle, pomVel, lastVel, lastPos;
        Quaternion pomRest;
        float squashT = 1f, squashAmount;
        Vector3 squashBaseScale = Vector3.one;
        bool hasParams;

        static readonly int RideState = Animator.StringToHash("Ride");
        static readonly int JumpState = Animator.StringToHash("Jump");
        static readonly int SplashState = Animator.StringToHash("Splash");
        static readonly int BumpState = Animator.StringToHash("Bump");
        static readonly string[] ArmBoneNames = { "arm.L", "hand.L", "arm.R", "hand.R" };
        const int ArmSamples = 24;
        Transform[] armBones;
        Quaternion[] armTable;
        float armClipLen = 1f, armW;
        /// <summary>Current arm-hold weight (0 = clip pose, 1 = Slide pose) - for tests / reviews.</summary>
        public float ArmHoldWeight => armW;

        Vector3 bobBasePos;
        Quaternion bobBaseRot = Quaternion.identity;
        float bobW, bobT;

        void Awake()
        {
            if (animator == null) animator = GetComponentInChildren<Animator>();
            if (pomPom == null) pomPom = FindDeep(transform, "pompom");
            if (squashRoot == null && animator != null) squashRoot = animator.transform;
            if (pomPom != null) pomRest = pomPom.localRotation;
            if (squashRoot != null) { squashBaseScale = squashRoot.localScale; bobBasePos = squashRoot.localPosition; bobBaseRot = squashRoot.localRotation; }
            hasParams = animator != null && animator.runtimeAnimatorController != null;
            if (hasParams) BuildArmTable();
        }

        /// <summary>Samples the Slide take's arm / hand rotations (ArmSamples phases) once, then restores the pose.</summary>
        void BuildArmTable()
        {
            AnimationClip clip = null;
            foreach (var c in animator.runtimeAnimatorController.animationClips)
                if (c != null && c.name == armHoldClip) { clip = c; break; }
            if (clip == null) { Debug.LogWarning("[BWK motion] arm hold: no '" + armHoldClip + "' clip - off"); return; }
            var all = animator.GetComponentsInChildren<Transform>(true);
            var bones = new System.Collections.Generic.List<Transform>();
            foreach (var n in ArmBoneNames)
                foreach (var t in all) if (t.name == n) { bones.Add(t); break; }
            if (bones.Count == 0) { Debug.LogWarning("[BWK motion] arm hold: no arm bones - off"); return; }
            var lp = new Vector3[all.Length]; var lr = new Quaternion[all.Length]; var ls = new Vector3[all.Length];
            for (int i = 0; i < all.Length; i++) { lp[i] = all[i].localPosition; lr[i] = all[i].localRotation; ls[i] = all[i].localScale; }
            int nb = bones.Count;
            var table = new Quaternion[ArmSamples * nb];
            float maxDelta = 0f;
            for (int s = 0; s < ArmSamples; s++)
            {
                clip.SampleAnimation(animator.gameObject, clip.length * s / ArmSamples);
                for (int b = 0; b < nb; b++)
                {
                    table[s * nb + b] = bones[b].localRotation;
                    maxDelta = Mathf.Max(maxDelta, Quaternion.Angle(bones[b].localRotation, lr[System.Array.IndexOf(all, bones[b])]));
                }
            }
            for (int i = 0; i < all.Length; i++) { all[i].localPosition = lp[i]; all[i].localRotation = lr[i]; all[i].localScale = ls[i]; }
            if (maxDelta < 1f)
            {
                // sampling did not move the arms (would hold them in the bind pose) -> leave the clips untouched
                Debug.LogWarning($"[BWK motion] arm hold: '{clip.name}' samples equal the bind pose ({maxDelta:F2} deg) - off");
                return;
            }
            armBones = bones.ToArray();
            armTable = table;
            armClipLen = Mathf.Max(0.1f, clip.length);
            Debug.Log($"[BWK motion] arm hold: {nb} bones from '{clip.name}' ({clip.length:F2} s), max sample delta from bind {maxDelta:F1} deg");
        }

        void OnEnable()
        {
            if (runner == null) return;
            runner.Jumped += OnJump;
            runner.Landed += OnLand;
            runner.Bumped += OnBump;
            runner.FinishedRun += OnFinish;
        }

        void OnDisable()
        {
            if (runner == null) return;
            runner.Jumped -= OnJump;
            runner.Landed -= OnLand;
            runner.Bumped -= OnBump;
            runner.FinishedRun -= OnFinish;
        }

        void OnJump() { Trigger(JumpId); Squash(-0.18f); }
        void OnLand() { Trigger(LandId); Squash(0.22f); }
        void OnBump() { Trigger(BumpId); Squash(0.15f); }
        // Finishing sequence (2026-11-26): the mascot first brakes to a stop in front of the portal; the celebration clip
        // starts when it begins its turn toward the camera (see Update), so the arms go up while it turns.
        void OnFinish() { celebrated = false; }
        bool celebrated;

        void Trigger(int id) { if (hasParams) animator.SetTrigger(id); }

        void Squash(float amount) { squashAmount = amount; squashT = 0f; }

        void Update()
        {
            if (!hasParams || runner == null) return;
            float dt = Time.deltaTime;
            animator.SetFloat(SteerId, runner.Steer, 0.06f, dt);
            animator.SetFloat(CurveId, runner.CurveSteer, 0.2f, dt);
            animator.SetFloat(SpeedId, runner.Speed / Mathf.Max(1f, runner.maxSpeed), 0.2f, dt);
            animator.SetBool(GroundedId, runner.Grounded);
            animator.SetBool(BoostId, runner.Boosting || runner.Frame.slope < -14f);
            animator.SetBool(RunningId, runner.State == RunnerState.Running);
            if (runner.State == RunnerState.Running) celebrated = false;
            else if (!celebrated && (runner.FinishTurning || (runner.State == RunnerState.Finished && runner.finishRestBeforeEnd <= 0f)))
            {
                celebrated = true;
                Trigger(CelebrateId);
                Squash(-0.14f); // stretch up into the happy hop
            }
        }

        void LateUpdate()
        {
            float dt = Mathf.Max(1e-4f, Time.deltaTime);
            bool running = runner != null && runner.State == RunnerState.Running;
            // Seated arm hold: blend the arm / hand bones back toward the Slide pose after the Animator wrote this frame.
            if (armBones != null && hasParams)
            {
                var st = animator.GetCurrentAnimatorStateInfo(0);
                int sh = st.shortNameHash;
                float target = 0f;
                if (running)
                {
                    if (sh == RideState) target = armHoldRide;
                    else if (sh == JumpState || sh == SplashState || sh == BumpState) target = armHoldAction;
                }
                armW = Mathf.MoveTowards(armW, target, dt * 3f);
                if (armW > 1e-3f)
                {
                    float ph = sh == RideState ? Mathf.Repeat(st.normalizedTime, 1f) : Mathf.Repeat(Time.time / armClipLen, 1f);
                    float fs = ph * ArmSamples;
                    int s0 = Mathf.FloorToInt(fs) % ArmSamples, s1 = (s0 + 1) % ArmSamples;
                    float u = fs - Mathf.Floor(fs);
                    int nb = armBones.Length;
                    for (int b = 0; b < nb; b++)
                    {
                        Quaternion q = Quaternion.Slerp(armTable[s0 * nb + b], armTable[s1 * nb + b], u);
                        armBones[b].localRotation = Quaternion.Slerp(armBones[b].localRotation, q, armW);
                    }
                }
            }
            // Gentle water bob on the model root while seated on the water (two detuned waves, a little roll / pitch).
            if (squashRoot != null && runner != null)
            {
                float bobTarget = running && runner.Grounded ? Mathf.Clamp01(0.4f + 0.6f * runner.Speed / Mathf.Max(1f, runner.maxSpeed)) : 0f;
                bobW = Mathf.MoveTowards(bobW, bobTarget, dt * 2f);
                bobT += dt;
                float w = 2f * Mathf.PI * bobFrequency * bobT;
                float y = bobAmplitude * bobW * (0.75f * Mathf.Sin(w) + 0.25f * Mathf.Sin(1.83f * w + 1.1f));
                float roll = bobRollDeg * bobW * Mathf.Sin(0.61f * w + 0.4f);
                float pitchB = bobPitchDeg * bobW * Mathf.Sin(w - 0.9f);
                squashRoot.localPosition = bobBasePos + Vector3.up * y;
                squashRoot.localRotation = bobBaseRot * Quaternion.Euler(pitchB, 0f, roll);
            }
            // Squash and stretch (volume-preserving) on the model root.
            if (squashRoot != null)
            {
                squashT = Mathf.Min(1f, squashT + dt / 0.35f);
                float s = squashAmount * Mathf.Sin(squashT * Mathf.PI) * (1f - squashT * 0.3f);
                squashRoot.localScale = Vector3.Scale(squashBaseScale, new Vector3(1f + s * 0.5f, 1f - s, 1f + s * 0.5f));
            }
            // Pom-pom spring: lags behind acceleration in the mascot's local space.
            if (pomPom != null && runner != null)
            {
                Vector3 pos = runner.transform.position;
                Vector3 vel = (pos - lastPos) / dt;
                Vector3 acc = (vel - lastVel) / dt;
                lastPos = pos; lastVel = vel;
                if (acc.sqrMagnitude > 4000f) acc = Vector3.zero; // ignore teleports
                Vector3 localAcc = runner.transform.InverseTransformDirection(acc);
                Vector3 target = new Vector3(Mathf.Clamp(localAcc.z * 0.9f, -pomMaxAngle, pomMaxAngle), 0f,
                                             Mathf.Clamp(-localAcc.x * 0.9f, -pomMaxAngle, pomMaxAngle));
                pomVel += (target - pomAngle) * pomStiffness * dt - pomVel * pomDamping * dt;
                pomAngle += pomVel * dt;
                // additive on top of the clip's own pom-pom follow-through (the Animator rewrites the pose every frame;
                // without a controller the rest pose is the base)
                Quaternion animated = hasParams ? pomPom.localRotation : pomRest;
                pomPom.localRotation = animated * Quaternion.Euler(pomAngle.x, 0f, pomAngle.z);
            }
        }

        static Transform FindDeep(Transform root, string nameContains)
        {
            foreach (var t in root.GetComponentsInChildren<Transform>(true))
                if (t.name.ToLowerInvariant().Contains(nameContains)) return t;
            return null;
        }
    }
}

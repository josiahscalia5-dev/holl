using System.Collections.Generic;
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

        // Motion E pass 9 (owner 10:48 / 12:08, reference 01 + crop 23b): seated on his bottom with the small arms raised
        // UP-OUTWARD beside the hat brim. Visual only, after the arm hold: each arm is aimed as a straight stubby limb at the
        // highest elevation whose upper arm, elbow and mitt stay clear of the knitted cuff (measured from the cuff vertices),
        // swung a little back so the rear camera sees the mitts beside the brim. Full in Ride / Accelerate, partial in the
        // jump / landing / bump reactions, 0 in the intro / finish / celebration (their clips stay untouched).
        [Header("Seated arms up-outward (visual only)")]
        public SeatedArmSettings seatedArms = new SeatedArmSettings();
        [Range(0f, 1f)] public float seatedArmsRide = 1f;
        [Range(0f, 1f)] public float seatedArmsAction = 0.5f;
        SeatedArmSolver armSolver;
        float seatW;
        /// <summary>Current seated-arms weight and the last solve (for tests / reviews).</summary>
        public float SeatedArmsWeight => seatW;
        public SeatedArmSolver ArmSolver => armSolver;

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
        static readonly int AccelState = Animator.StringToHash("Accelerate");
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
            if (hasParams)
            {
                armSolver = SeatedArmSolver.Create(animator.transform);
                if (armSolver == null) Debug.LogWarning("[BWK motion] seated arms: bones / cuff not found - off");
                else Debug.Log("[BWK motion] seated arms: " + armSolver.Describe());
            }
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
            // Seated arms raised up-outward beside the brim (collision-aware aim on top of the clip / hold pose).
            if (armSolver != null && hasParams)
            {
                var st = animator.GetCurrentAnimatorStateInfo(0);
                int sh = st.shortNameHash;
                float target = 0f;
                if (running)
                {
                    if (sh == RideState || sh == AccelState) target = seatedArmsRide;
                    else if (sh == JumpState || sh == SplashState || sh == BumpState) target = seatedArmsAction;
                }
                seatW = Mathf.MoveTowards(seatW, target, dt * 2.5f);
                if (seatW > 1e-3f)
                {
                    float ph = sh == RideState ? Mathf.Repeat(st.normalizedTime, 1f) : Mathf.Repeat(Time.time / armClipLen, 1f);
                    armSolver.Apply(seatW, seatedArms, ph);
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

    /// <summary>Motion E pass 9: tunables of the seated up-outward arm pose (MascotAnimatorDriver.seatedArms).</summary>
    [System.Serializable]
    public class SeatedArmSettings
    {
        [Tooltip("Highest straight-arm raise above horizontal (deg); the cuff check lowers it until the arm clears the hat.")]
        public float elevationDeg = 46f;
        [Tooltip("Lowest raise tried before the shoulder may slide outward (deg).")]
        public float minElevationDeg = 6f;
        [Tooltip("The forearm / mitt bends this much further up than the upper arm (deg).")]
        public float forearmExtraDeg = 14f;
        [Tooltip("Arms swing this far back toward the rear camera (deg), so the mitts read beside the brim.")]
        public float backDeg = 12f;
        [Tooltip("Character-left arm sits this much lower than the right (deg): the reference's natural asymmetry.")]
        public float asymmetryDeg = 8f;
        [Tooltip("Slow alternating arm wave with the ride phase (deg).")]
        public float waveDeg = 4f;
        [Tooltip("Gap kept between the arm / mitt surface and the knitted cuff / hat (m).")]
        public float clearance = 0.01f;
        [Tooltip("If no raise clears the hat, the shoulder may slide outward up to this fraction of the cuff radius.")]
        public float maxShoulderOut = 0.15f;
    }

    /// <summary>
    /// Motion E pass 9: collision-aware seated arm pose. Measures the mitts (hand-bone vertices) and the knitted cuff
    /// (vertices of the M_HatCuff* sub-mesh) once from the skinned meshes' bind data; per frame it aims each arm as a stubby
    /// limb up-outward at the highest elevation whose upper arm, elbow, forearm and mitt stay outside the hat (cuff radius,
    /// from the brim's lower edge upward). Used by MascotAnimatorDriver at runtime and by AnimatorBuilder to bake the
    /// seated "Slide" clip (so stills, the Ride blend centre and the arm hold all show the same pose).
    /// </summary>
    public class SeatedArmSolver
    {
        readonly Transform root;
        readonly Transform[] arm = new Transform[2], hand = new Transform[2];
        readonly Vector3[] mittLocal = new Vector3[2], armRestLocalPos = new Vector3[2];
        readonly float[] mittRadius = new float[2], armRadius = new float[2];
        readonly int[] mittCount = new int[2];
        Transform[] cuffBone;
        Vector3[] cuffLocal, cuffWorld;
        /// <summary>Last solve per side (0 = .L, 1 = .R): raise used (deg, NaN = no safe raise), shoulder slide (m), clearance (m).</summary>
        public readonly float[] LastElevation = { float.NaN, float.NaN }, LastShoulderOut = new float[2], LastClearance = new float[2];
        /// <summary>Last measured cuff radius / height (world m).</summary>
        public float CuffRadius { get; private set; }
        public float CuffHeight { get; private set; }

        SeatedArmSolver(Transform root) { this.root = root; }

        public static SeatedArmSolver Create(Transform root)
        {
            if (root == null) return null;
            var all = root.GetComponentsInChildren<Transform>(true);
            Transform Find(string n) { foreach (var t in all) if (t.name == n) return t; return null; }
            var s = new SeatedArmSolver(root);
            s.arm[0] = Find("arm.L"); s.hand[0] = Find("hand.L"); s.arm[1] = Find("arm.R"); s.hand[1] = Find("hand.R");
            for (int i = 0; i < 2; i++)
                if (s.arm[i] == null || s.hand[i] == null || s.hand[i].parent != s.arm[i]) return null;
            var handPts = new[] { new List<Vector3>(), new List<Vector3>() };
            var armSq = new double[2]; var armN = new int[2];
            var cb = new List<Transform>(); var cl = new List<Vector3>();
            foreach (var smr in root.GetComponentsInChildren<SkinnedMeshRenderer>(true))
            {
                var mesh = smr.sharedMesh;
                if (mesh == null || !mesh.isReadable) continue;
                var bones = smr.bones; var bp = mesh.bindposes; var bw = mesh.boneWeights; var v = mesh.vertices;
                if (bw.Length != v.Length || bp.Length != bones.Length) continue;
                for (int i = 0; i < v.Length; i++)
                {
                    int b = bw[i].boneIndex0;
                    if (b < 0 || b >= bones.Length || bw[i].weight0 < 0.5f) continue;
                    var t = bones[b];
                    for (int side = 0; side < 2; side++)
                    {
                        if (t == s.hand[side]) handPts[side].Add(bp[b].MultiplyPoint3x4(v[i]));
                        else if (t == s.arm[side])
                        {
                            // distance of the upper-arm vertex from the shoulder -> elbow line (arm-local)
                            Vector3 p = bp[b].MultiplyPoint3x4(v[i]);
                            Vector3 axis = s.hand[side].localPosition.normalized;
                            armSq[side] += (p - axis * Vector3.Dot(p, axis)).sqrMagnitude; armN[side]++;
                        }
                    }
                }
                var mats = smr.sharedMaterials;
                for (int k = 0; k < mesh.subMeshCount && k < mats.Length; k++)
                {
                    if (mats[k] == null || !mats[k].name.StartsWith("M_HatCuff")) continue;
                    var tris = mesh.GetTriangles(k);
                    int step = Mathf.Max(1, tris.Length / 900);
                    for (int j = 0; j < tris.Length; j += step)
                    {
                        int i = tris[j]; int b = bw[i].boneIndex0;
                        if (b < 0 || b >= bones.Length) continue;
                        cb.Add(bones[b]); cl.Add(bp[b].MultiplyPoint3x4(v[i]));
                    }
                }
            }
            if (cb.Count < 12) return null;
            for (int side = 0; side < 2; side++)
            {
                var pts = handPts[side];
                if (pts.Count < 8) return null;
                // mitt = the far quarter of the hand-bone vertices (forearm + mitt share the hand bone)
                pts.Sort((a, b) => a.sqrMagnitude.CompareTo(b.sqrMagnitude));
                int from = pts.Count * 3 / 4; Vector3 c = Vector3.zero;
                for (int i = from; i < pts.Count; i++) c += pts[i];
                c /= pts.Count - from;
                double sq = 0; for (int i = from; i < pts.Count; i++) sq += (pts[i] - c).sqrMagnitude;
                s.mittLocal[side] = c; s.mittCount[side] = pts.Count;
                s.mittRadius[side] = Mathf.Sqrt((float)(sq / (pts.Count - from)));
                s.armRadius[side] = armN[side] > 0 ? Mathf.Sqrt((float)(armSq[side] / armN[side])) : s.mittRadius[side] * 0.8f;
                s.armRestLocalPos[side] = s.arm[side].localPosition;
            }
            s.cuffBone = cb.ToArray(); s.cuffLocal = cl.ToArray(); s.cuffWorld = new Vector3[cl.Count];
            return s;
        }

        public string Describe() =>
            $"mitt verts L {mittCount[0]} R {mittCount[1]}, mitt r {mittRadius[0]:F3}/{mittRadius[1]:F3}, arm r {armRadius[0]:F3}/{armRadius[1]:F3}, " +
            $"upper arm {hand[0].localPosition.magnitude:F3}/{hand[1].localPosition.magnitude:F3}, mitt dist {mittLocal[0].magnitude:F3}/{mittLocal[1].magnitude:F3} (bone units), cuff pts {cuffLocal.Length}";

        public string LastSolve() =>
            $"cuff R {CuffRadius:F3} h {CuffHeight:F3}; L raise {LastElevation[0]:F1} slide {LastShoulderOut[0]:F3} clear {LastClearance[0]:F3}; " +
            $"R raise {LastElevation[1]:F1} slide {LastShoulderOut[1]:F3} clear {LastClearance[1]:F3}";

        /// <summary>Poses both arms on top of the current (clip) pose; weight 0..1, phase 0..1 of the ride cycle.</summary>
        public void Apply(float weight, SeatedArmSettings set, float phase)
        {
            if (weight <= 0f || set == null) return;
            Vector3 A = root.up;
            Vector3 C = Vector3.zero;
            int n = cuffLocal.Length;
            for (int i = 0; i < n; i++) { cuffWorld[i] = cuffBone[i].TransformPoint(cuffLocal[i]); C += cuffWorld[i]; }
            C /= n;
            float Rc = 0f, yb = float.MaxValue, yt = float.MinValue;
            for (int i = 0; i < n; i++)
            {
                Vector3 d = cuffWorld[i] - C; float h = Vector3.Dot(d, A);
                Rc = Mathf.Max(Rc, (d - A * h).magnitude); yb = Mathf.Min(yb, h); yt = Mathf.Max(yt, h);
            }
            CuffRadius = Rc; CuffHeight = yt - yb;
            Vector3 fwd = Vector3.ProjectOnPlane(root.forward, A).normalized;
            float cl = set.clearance;
            // clearance of a sphere from the hat: everything from the brim's lower edge up must stay outside the cuff radius
            float Clear(Vector3 p, float r)
            {
                Vector3 d = p - C; float h = Vector3.Dot(d, A);
                if (h < yb - r - cl) return (yb - r - cl) - h + 1f;
                return (d - A * h).magnitude - (Rc + r + cl);
            }
            for (int side = 0; side < 2; side++)
            {
                Transform a = arm[side], hd = hand[side];
                a.localPosition = armRestLocalPos[side];
                Vector3 S = a.position, E = hd.position, M = hd.TransformPoint(mittLocal[side]);
                float L1 = (E - S).magnitude, L2 = (M - E).magnitude;
                Vector3 lat = Vector3.ProjectOnPlane(S - C, A);
                if (lat.sqrMagnitude < 1e-10f || L1 < 1e-5f || L2 < 1e-5f) { LastElevation[side] = float.NaN; continue; }
                lat.Normalize();
                float back = set.backDeg * Mathf.Deg2Rad;
                Vector3 outDir = (lat * Mathf.Cos(back) - fwd * Mathf.Sin(back)).normalized;
                float rm = mittRadius[side] * Mathf.Abs(hd.lossyScale.x), ra = armRadius[side] * Mathf.Abs(a.lossyScale.x);
                float eTop = set.elevationDeg + (side == 0 ? -0.5f : 0.5f) * set.asymmetryDeg
                             + set.waveDeg * Mathf.Sin(2f * Mathf.PI * phase + side * Mathf.PI);
                float chosenE = float.NaN, chosenO = 0f, chosenC = 0f;
                for (int pass = 0; pass < 4 && float.IsNaN(chosenE); pass++)
                {
                    float o = pass * set.maxShoulderOut * Rc / 3f;
                    Vector3 Sp = S + lat * o;
                    for (float e = eTop; e >= set.minElevationDeg - 1e-3f; e -= 2f)
                    {
                        float e1 = e * Mathf.Deg2Rad, e2 = (e + set.forearmExtraDeg) * Mathf.Deg2Rad;
                        Vector3 d1 = outDir * Mathf.Cos(e1) + A * Mathf.Sin(e1), d2 = outDir * Mathf.Cos(e2) + A * Mathf.Sin(e2);
                        Vector3 E2 = Sp + d1 * L1, M2 = E2 + d2 * L2;
                        float c = Mathf.Min(Mathf.Min(Clear(Sp + d1 * (0.6f * L1), ra), Clear(E2, ra)),
                                            Mathf.Min(Clear(E2 + d2 * (0.5f * L2), ra), Clear(M2, rm)));
                        if (c >= 0f) { chosenE = e; chosenO = o; chosenC = c; break; }
                    }
                }
                LastElevation[side] = chosenE; LastShoulderOut[side] = chosenO; LastClearance[side] = chosenC;
                if (float.IsNaN(chosenE)) continue;   // no safe raise: keep the clip's own arm pose
                if (chosenO > 0f)
                    a.localPosition = armRestLocalPos[side] + (a.parent != null ? a.parent.InverseTransformVector(lat * chosenO) : lat * chosenO) * weight;
                float r1 = chosenE * Mathf.Deg2Rad, r2 = (chosenE + set.forearmExtraDeg) * Mathf.Deg2Rad;
                Vector3 t1 = outDir * Mathf.Cos(r1) + A * Mathf.Sin(r1), t2 = outDir * Mathf.Cos(r2) + A * Mathf.Sin(r2);
                Quaternion q1 = Quaternion.FromToRotation(hd.position - a.position, t1);
                a.rotation = Quaternion.Slerp(a.rotation, q1 * a.rotation, weight);
                Vector3 E3 = hd.position, M3 = hd.TransformPoint(mittLocal[side]);
                Quaternion q2 = Quaternion.FromToRotation(M3 - E3, t2);
                hd.rotation = Quaternion.Slerp(hd.rotation, q2 * hd.rotation, weight);
            }
        }
    }
}

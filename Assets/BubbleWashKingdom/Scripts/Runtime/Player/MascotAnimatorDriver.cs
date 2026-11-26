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

        void Awake()
        {
            if (animator == null) animator = GetComponentInChildren<Animator>();
            if (pomPom == null) pomPom = FindDeep(transform, "pompom");
            if (squashRoot == null && animator != null) squashRoot = animator.transform;
            if (pomPom != null) pomRest = pomPom.localRotation;
            if (squashRoot != null) squashBaseScale = squashRoot.localScale;
            hasParams = animator != null && animator.runtimeAnimatorController != null;
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

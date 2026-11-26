# Agent: Agent 4 lighting & visual quality

Agent adf64bfb7be8cbfb1, lead session b3410996-81ad-4e2d-9d43-bf3d56c2a918, started 2026-11-26 02:20 UTC.

_Text-only export: the lead's brief, the agent's statements and one line per tool action (no tool outputs, images, hidden reasoning or system context; e-mails and tokens redacted)._

### Brief from the lead (2026-11-26 02:20 UTC)

You are AGENT 4 - LIGHTING AND VISUAL QUALITY, one of four specialist agents improving the Unity game "Bubble Wash Kingdom" (Unity 6.3 URP, portrait 9:16) in C:\Users\josia\thanksgiving. The lead developer (the main session) coordinates you and is the ONLY one who builds/saves the main scene. Follow the project CLAUDE.md (never use the reference video or frames as textures, Reference/ is private). The project's Claude Unity Game Studio skills are available to you through the Skill tool: unity-lighting-vfx, unity-graphics, unity-performance - load the relevant one before deep URP lighting / post work.

OWNER DIRECTIVE (highest priority): achieve the closest possible visual match to the owner's approved Google Flow video. Visual quality beats token cost, development effort and mobile optimization. Target 9-10/10 similarity. Do not claim success without actual rendered evidence. Keep the computer stable and normal security protections intact.

GOAL: give the HERO GAMEPLAY SCREEN (rear camera inside the tunnel; mascot sits on his bottom, feet forward, back to the camera - never change that) the reference's premium animated-film lighting: glowing neon, warm marquee bulbs, polished gold reflections, bloom, saturated candy palette.

REFERENCE (do NOT re-analyse the whole video, use only these): Reference/frames/f_003.00s.png (hero target), Reference/frames/f_001.75s.png, Reference/key/04_very_middle_7.52s.png, 05_side_chambers_10.5s.png, 06_ending_portal_15.0s.png, Reference/contact_sheet_*.jpg (overview).
CURRENT STATE: Captures/compare/hero_vs_reference_9x16.png and _16x9.png (LEFT = reference, RIGHT = our real Unity render), Captures/stills/*.png.

YOUR FILES (edit ONLY these): Assets/BubbleWashKingdom/Scripts/Editor/SceneBuilder.Lighting.cs (BuildLighting: key light, ambient, fog, fill lights, reflection probes, post-processing volume; BuildCharacterLights - keep every character light under the "CharacterLights" child; AddPoint; BakeProbes; BuildNeonStars placement / density / orientation); MaterialLibrary.Lighting.cs (M_Gold, M_GoldDark, M_Coin, M_Gem, M_Bulb, M_Neon*); Assets/BubbleWashKingdom/Art/Shaders/BWK_Gold.shader, BWK_Emissive.shader; BWKCommon.hlsl (shared include used by every custom shader: additive, backward-compatible changes only); Assets/Settings/*.asset (URP pipeline / renderer quality: HDR, MSAA, shadows, post - you may raise PC quality; keep the Mobile asset sane); you may add new lighting shaders Assets/BubbleWashKingdom/Art/Shaders/BWK_Light*.shader and new runtime lighting scripts under Scripts/Runtime/FX/Lighting*.cs. Never edit, delete, revert or reformat anyone else's files; put needed changes elsewhere in your report under "lead requests". Never git commit/push/reset/checkout/stash. Never run SceneBuilder.BuildAllBatch (lead only); never save the scene. Camera framing (RunnerCameraRig) belongs to the lead.

HEAVY PROCESSES (4-thread / 7.7 GB laptop shared by four agents): never start Unity or Blender directly. Use only:
  * Unity no-save preview: bash Tools/unity_run.sh BubbleWash.EditorTools.CaptureTools.AgentPreviewBatch <logname> -bwkOut Captures/agents/lighting
It waits on a project-wide lock (another agent may hold it for minutes): call it with the Bash tool using timeout 600000 or run_in_background true and wait for the completion notification; never loop-poll, never kill other processes, never delete Logs/heavy.lock unless the script itself reports it stale. Batch several changes into each run. The preview regenerates textures and all materials, re-imports changed shaders, rebuilds YOUR lighting / post / reflection probes / character lights in memory (SceneBuilder.PreviewRefreshDomains), then writes hero_9x16.png, hero_16x9.png and side-by-side comparisons into your folder, so you can iterate on lighting directly. Neon star PLACEMENT changes (BuildNeonStars) appear only after the lead's integration build (ask the lead via SendMessage to "main"); star colours / glow show immediately. C# SAFETY: a C# compile error breaks every Unity run for everyone, so keep every .cs edit compilable and check the preview summary for "error CS"; check for "Shader error" too.

GAPS vs the reference, most visible first:
 1. BULBS: ours are pale yellow flat dots; reference = warm golden marquee bulbs with white-hot cores and soft orange bloom halos all around each gold ring (BWK_Emissive, M_Bulb; bloom in the post volume). Agent 3 is rebuilding the ring/bulb geometry; you own their emissive look.
 2. NEON STARS: thick tubes now but pastel; reference = saturated neon yellow / cyan / pink tubes with bright cores and strong glow, some double-line stars, scattered densely on the tunnel walls and ceiling at varied sizes and angles.
 3. OVERALL LOOK: reference is bright, saturated, high-key candy palette with strong bloom and warm-gold vs violet contrast, glossy reflections everywhere; ours is a bit darker with weak glow. Tune post (bloom, tonemapping, colour adjustments, vignette, maybe SSAO / lens effects if they help), key light, ambient, fog and reflection probes for a premium animated-film look. Avoid washing everything out.
 4. GOLD: BWK_Gold (procedural matcap + light speculars) on rings, coins, couplers: make it read like polished jewellery gold with crisp highlights, warm bulb glints and soft reflections of the violet tunnel.
 5. MASCOT LIGHTING: warm top / rim light on the hat and fur like the reference (character lights ride with the runner).
Do as many refinement passes as needed to get close to the reference.

FINAL REPORT (your last message): what you changed (files), evidence (paths of your best preview images), remaining differences vs the reference, lead requests (exact file / function / values), cost notes, and an honest 1-10 similarity score for your domain.

**Agent (2026-11-26 02:20 UTC):**

> _tool: mcp__ccd_turn__update_plan_

**Agent (2026-11-26 02:21 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Reference\frames\f_003.00s.png_

**Agent (2026-11-26 02:21 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\compare\hero_vs_reference_9x16.png_

**Agent (2026-11-26 02:21 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\compare\hero_vs_reference_16x9.png_

**Agent (2026-11-26 02:21 UTC):**

> _tool: Bash - List captures and reference key files_

**Agent (2026-11-26 02:21 UTC):**

> _tool: Bash - List project scripts, shaders, settings_

**Agent (2026-11-26 02:21 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Scripts\Editor\SceneBuilder.Lighting.cs_

**Agent (2026-11-26 02:21 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Scripts\Editor\MaterialLibrary.Lighting.cs_

**Agent (2026-11-26 02:21 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Art\Shaders\BWK_Gold.shader_

**Agent (2026-11-26 02:21 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Art\Shaders\BWK_Emissive.shader_

**Agent (2026-11-26 02:21 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Art\Shaders\BWKCommon.hlsl_

**Agent (2026-11-26 02:21 UTC):**

> _tool: Bash - Find material helper signatures_

**Agent (2026-11-26 02:21 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Scripts\Editor\MaterialLibrary.cs_

**Agent (2026-11-26 02:21 UTC):**

> _tool: Bash - Find preview batch and refresh domains code_

**Agent (2026-11-26 02:21 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Scripts\Editor\CaptureTools.cs_

**Agent (2026-11-26 02:21 UTC):**

> _tool: Bash - Show PC URP pipeline asset_

**Agent (2026-11-26 02:21 UTC):**

> _tool: Bash - Show PC renderer and quality settings_

**Agent (2026-11-26 02:21 UTC):**

> _tool: Bash - Map settings GUIDs and quality defaults_

**Agent (2026-11-26 02:21 UTC):**

> _tool: Bash - Check quality level usage and Mobile vs PC asset diff_

**Agent (2026-11-26 02:21 UTC):**

> _tool: Bash - Read ProjectSetup quality logic and renderer diff_

**Agent (2026-11-26 02:22 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\agents\_lead_test\hero_vs_reference_9x16.png_

**Agent (2026-11-26 02:22 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Reference\frames\f_001.75s.png_

**Agent (2026-11-26 02:22 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Reference\key\04_very_middle_7.52s.png_

**Agent (2026-11-26 02:22 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Reference\key\05_side_chambers_10.5s.png_

**Agent (2026-11-26 02:22 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Reference\key\06_ending_portal_15.0s.png_

**Agent (2026-11-26 02:22 UTC):**

> _tool: Bash - Grep art bible for lighting keywords_

**Agent (2026-11-26 02:22 UTC):**

> _tool: Bash - Locate visual analysis art bible_

**Agent (2026-11-26 02:22 UTC):**

> _tool: Bash - Find usages of my materials and lights elsewhere_

**Agent (2026-11-26 02:22 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Assets\BubbleWashKingdom\Scripts\Editor\SceneBuilder.Environment.cs_

**Agent (2026-11-26 02:22 UTC):**

> _tool: Bash - Survey lighting usage across custom shaders_

**Agent (2026-11-26 02:22 UTC):**

> _tool: Skill_

### Message (2026-11-26 02:22 UTC)

Base directory for this skill: C:\Users\josia\thanksgiving\.claude\skills\unity-lighting-vfx

# Unity Lighting and Visual Effects

## Lighting Modes

Unity provides three light modes controlling how illumination is calculated.

### Realtime Lights
- Calculate lighting **every frame at runtime**
- Allow dynamic changes to intensity, color, position
- Cast shadows up to Shadow Distance
- Contribute only direct lighting by default (no bounced light)
- Higher runtime cost, especially in complex scenes or low-end hardware
- Best for: dynamic objects, flickering effects, moving light sources

### Baked Lights
- Calculations performed **in the Unity Editor** and saved as lighting data to disk
- At runtime, Unity loads pre-computed data instead of calculating dynamically
- Bake both direct and indirect lighting into lightmaps
- Store information in Light Probes for moving objects
- Cannot modify light properties at runtime; do not illuminate dynamic GameObjects
- No specular contributions
- Best for: static scenery, complex indirect lighting, performance-critical scenarios

### Mixed Lights
- Combine **baked indirect lighting** with **real-time direct lighting**
- Behavior depends on the Lighting Mode setting in the Lighting window
- Cast real-time shadows (not baked soft shadows)
- Can change properties at runtime (affects real-time component only)
- Always more expensive than fully baked lighting
- Best for: dynamic shadows with baked background lighting

**Important:** All baked/mixed modes require **Baked Global Illumination** enabled. Without it, Mixed and Baked lights behave as Realtime.

## Light Types

### Directional Light
- Located infinitely far away, emits light in one direction
- Parallel rays, no distance-based intensity falloff
- Simulates sun/moon; every new scene includes one by default
- Links to procedural sky system; rotate to create time-of-day effects

### Point Light
- Located at a point, emits in all directions equally
- Intensity follows inverse square law (diminishes with distance squared)
- Use for lamps, explosions, local illumination

### Spot Light
- Located at a point, emits in a cone shape
- Adjustable cone angle; light diminishes at edges (penumbra)
- Wider angles create larger fade areas
- Use for flashlights, headlights, searchlights

### Area Light
- Defined by a rectangle or disc; emits uniformly across surface
- Follows inverse square law; produces soft, subtle shading
- **Bake-only** -- not available at runtime
- Use for street lights, realistic interior lighting

## Global Illumination

Global illumination (GI) simulates how light bounces between surfaces, producing realistic indirect lighting.

### Baked GI
- Pre-computes indirect lighting into lightmaps using the **Progressive Lightmapper** (CPU or GPU)
- Results stored in lightmap textures and Light Probes
- Configure in the Lighting window under **Bake** settings
- GPU Progressive Lightmapper offers faster bake times with configurable tile sizes

### Environment Lighting
Three ambient light sources configured in the Lighting window Environment tab:
- **Skybox**: Uses skybox material colors for ambient light from different angles
- **Gradient**: Separate sky, horizon, and ground colors with smooth blending
- **Color**: Uniform ambient light across the scene

Intensity Multiplier (0-8, default 1) controls ambient brightness.

### Environment Reflections
- Source: Skybox or custom Cubemap/RenderTexture
- Configurable resolution, compression, intensity multiplier
- Bounces setting controls reflection evaluation iterations between objects

## Light Probes and Adaptive Probe Volumes

### Light Probes
- Capture lighting information in **empty space** throughout a scene
- At runtime, indirect lighting for dynamic GameObjects is approximated using nearest probes
- Provide indirect bounced light for moving objects and LOD system support
- Must be manually placed using Light Probe Groups
- Store baked lighting information; work with both direct and indirect lighting

### Adaptive Probe Volumes (APV)
APV is the modern replacement for manual Light Probe placement in URP:
- **Automated probe placement** -- eliminates manual Light Probe Group positioning
- **Per-pixel lighting** -- superior quality compared to per-object approaches
- **Scene baking** -- bake multiple scenes together using Baking Sets
- **Runtime adjustments** -- Lighting Scenarios and sky occlusion for dynamic changes
- **Large-world support** -- streaming data for expansive open-world environments
- **Data flexibility** -- loading from AssetBundles or Addressables
- Configurable probe density and volume size with visualization tools

## Reflection Probes

Capture a spherical view of surroundings as a cubemap for reflective materials.

### Types
| Type | Description |
|------|-------------|
| **Baked** | Captures static GameObjects only; best performance |
| **Custom** | Allows dynamic object capture with custom textures |
| **Realtime** | Updates during gameplay; configurable refresh mode |

### Key Properties
- **Importance**: Rendering priority when multiple probes overlap
- **Intensity**: Texture brightness in shader calculations
- **Box Projection**: Enables projection mapping for interiors (requires URP config)
- **Box Size/Offset**: World-space bounding box for reflection contribution
- **Blend Distance**: Blending distance for deferred probes

### Realtime Options
- **Refresh Mode**: On Awake, Every Frame, or Via Scripting
- **Time Slicing**: All Faces At Once, Individual Faces, No Time Slicing

## Particle System vs VFX Graph

| Feature | Particle System | VFX Graph |
|---------|----------------|-----------|
| Simulation | CPU-based | GPU-based |
| Particle count | Thousands | Millions |
| Render pipeline | All pipelines | URP/HDRP only |
| Authoring | Inspector modules | Node-based graph editor |
| Physics | Built-in collision | Custom collision blocks |
| Scripting | Full C# API | Event-based C# API |
| Sub-emitters | Native support | GPU Event contexts |
| Best for | Small/medium effects, mobile | Large-scale effects, high-end |

**Decision Guide:**
- Use **Particle System** for mobile targets, simple effects, when you need full CPU-side scripting control, or when targeting the Built-in Render Pipeline
- Use **VFX Graph** for massive particle counts, GPU-driven simulations, complex node-based authoring, or high-end platforms with URP/HDRP

## Particle System Modules

| Module | Purpose |
|--------|---------|
| **Main** | Initial state: lifetime, speed, size, gravity, simulation space |
| **Emission** | Rate and timing of particle spawns |
| **Shape** | Volume/surface for emission and start velocity direction |
| **Velocity over Lifetime** | Modify movement over particle age |
| **Noise** | Turbulence for organic, chaotic motion |
| **Limit Velocity over Lifetime** | Natural deceleration |
| **Force over Lifetime** | Simulated physics forces |
| **Inherit Velocity** | Sub-emitter particles match parent velocity |
| **Lifetime by Emitter Speed** | Adjust lifespan based on emitter velocity |
| **Color over Lifetime / by Speed** | Color changes based on age or velocity |
| **Size over Lifetime / by Speed** | Dimension changes based on time or speed |
| **Rotation over Lifetime / by Speed** | Orientation changes |
| **Collision** | Particle collisions with scene geometry |
| **Triggers** | Designate particles as collision triggers |
| **Sub Emitters** | Particles that emit other particles |
| **Texture Sheet Animation** | Texture grid animation frames |
| **Trails** | Motion trail rendering |
| **Lights** | Real-time lights on particles |
| **External Forces** | Wind zones and force fields |
| **Renderer** | Image/mesh transform, shading, overdraw |
| **Custom Data** | Attach custom data to particles |

## VFX Graph Basics

### Systems
1. **Spawn System**: Single Spawn Context managing emission
2. **Particle System**: Initialize -> Update -> Output succession
3. **Mesh Output System**: Single Mesh Output Context

### Contexts
- **Spawn**: Executes each frame to calculate spawn amounts. States: Running, Idle, Waiting. Configurable loop duration, count, and delays
- **Initialize**: Runs at particle birth, sets initial state. Processes Blocks for newly spawned particles. Configurable bounds and capacity
- **Update**: Per-frame for all living particles. Automatic: position integration, rotation integration, aging, reaping
- **Output**: Renders particles (Quad, Mesh, etc.). No output ports. Customizable rendering blocks

### Graph Elements
- **Blocks**: Stackable nodes within Contexts; each handles one operation; top-to-bottom execution
- **Operators**: Low-level property workflow nodes connecting to Block/Context ports
- **Properties**: Connectable via property workflow
- **Settings**: Non-connectable editable values per Context

### GPU Events
Experimental feature where GPU computes events (vs CPU for normal events). Cannot be customized with Blocks.

## Common Patterns (C#)

### Create and Configure a Light
```csharp
using UnityEngine;

public class LightSetup : MonoBehaviour
{
    void Start()
    {
        GameObject lightObj = new GameObject("Dynamic Light");
        Light light = lightObj.AddComponent<Light>();
        light.type = LightType.Point;
        light.color = Color.yellow;
        light.intensity = 2.0f;
        light.range = 15f;
        light.shadows = LightShadows.Soft;
        light.shadowResolution = UnityEngine.Rendering.LightShadowResolution.Medium;
    }
}
```

### Create a Realtime Reflection Probe
```csharp
using UnityEngine;
using UnityEngine.Rendering;

public class ProbeSetup : MonoBehaviour
{
    void Start()
    {
        GameObject probeObj = new GameObject("Realtime Reflection Probe");
        ReflectionProbe probe = probeObj.AddComponent<ReflectionProbe>();
        probe.size = new Vector3(10, 10, 10);
        probe.mode = ReflectionProbeMode.Realtime;
        probe.refreshMode = ReflectionProbeRefreshMode.EveryFrame;
        probe.resolution = 256;
        probe.hdr = true;
    }
}
```

### Control Particle System at Runtime
```csharp
using UnityEngine;

public class ParticleController : MonoBehaviour
{
    ParticleSystem ps;

    void Start()
    {
        ps = GetComponent<ParticleSystem>();

        // Modify emission rate -- cache module in local variable first
        var emission = ps.emission;
        emission.rateOverTimeMultiplier = 50f;

        // Modify main module
        var main = ps.main;
        main.startLifetime = 3f;
        main.startSpeed = 5f;
        main.simulationSpace = ParticleSystemSimulationSpace.World;
    }

    void OnTriggerEnter(Collider other)
    {
        // Burst emit particles
        ps.Emit(100);
    }

    void OnDisable()
    {
        ps.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);
    }
}
```

### VFX Graph Runtime Control
```csharp
using UnityEngine;
using UnityEngine.VFX;

public class VFXController : MonoBehaviour
{
    VisualEffect vfx;
    VFXEventAttribute eventAttr;

    void Start()
    {
        vfx = GetComponent<VisualEffect>();
        eventAttr = vfx.CreateVFXEventAttribute();

        // Set exposed properties
        vfx.SetFloat("SpawnRate", 100f);
        vfx.SetVector3("Direction", Vector3.up);
        vfx.playRate = 1.5f;
    }

    void OnTriggerEnter(Collider other)
    {
        // Send custom event with attributes
        eventAttr.SetVector3("position", other.transform.position);
        vfx.SendEvent("OnHit", eventAttr);
    }

    public void StopEffect()
    {
        vfx.Stop();
    }
}
```

### Refresh Reflection Probe on Demand
```csharp
using UnityEngine;

public class ProbeRefresher : MonoBehaviour
{
    ReflectionProbe probe;

    void Start()
    {
        probe = GetComponent<ReflectionProbe>();
        probe.refreshMode = UnityEngine.Rendering.ReflectionProbeRefreshMode.ViaScripting;
    }

    public void RefreshReflections()
    {
        probe.RenderProbe();
    }

    public bool IsReady()
    {
        return probe.IsFinishedRendering(probe.RenderProbe());
    }
}
```

## Anti-Patterns

### Lighting Anti-Patterns
1. **Too many Realtime lights**: Each realtime light adds per-frame cost. Use Baked or Mixed for static lights
2. **Forgetting to enable Baked Global Illumination**: Mixed/Baked lights silently fall back to Realtime without it
3. **Overlapping Reflection Probes without Importance values**: Causes flickering; always set Importance to establish priority
4. **Using Area Lights expecting runtime behavior**: Area lights are bake-only; they produce no light at runtime
5. **Ignoring Indirect Multiplier**: Leaving at default can cause over-bright or too-dark bounced light; tune per light
6. **Not setting Shadow Bias correctly**: Too low causes self-shadowing artifacts (shadow acne); too high causes peter-panning (shadows detach from objects)
7. **Manual Light Probe placement in large scenes**: Use Adaptive Probe Volumes (APV) in URP instead for automated, per-pixel quality

### Particle System Anti-Patterns
1. **Not caching module references**: Each property access on a module struct immediately writes to native code; cache the module variable
2. **Using World simulation space for attached effects**: Particles drift away from moving parents; use Local space for attached FX
3. **Excessive particle counts on CPU**: Particle System is CPU-bound; for >10K particles, consider VFX Graph
4. **Forgetting to Stop/Clear**: Leaked particle systems consume CPU even when invisible

### VFX Graph Anti-Patterns
1. **Using VFX Graph for simple effects on mobile**: GPU overhead and URP/HDRP requirement make it overkill for simple mobile effects
2. **Not setting Capacity in Initialize**: Default capacity may allocate too much or too little GPU memory
3. **Ignoring Bounds**: Incorrect bounds cause effects to be culled when visible; always configure bounds in Initialize context
4. **Sending events every frame without throttling**: SendEvent has CPU-GPU sync cost; batch or throttle event dispatch

## Key API Quick Reference

### Light (UnityEngine.Light)
| Member | Type | Description |
|--------|------|-------------|
| `type` | Property | LightType (Directional, Point, Spot, Area) |
| `color` | Property | Emitted light color |
| `intensity` | Property | Brightness multiplier |
| `range` | Property | Max distance (Point/Spot) |
| `spotAngle` / `innerSpotAngle` | Property | Outer/inner cone angles |
| `shadows` | Property | LightShadows (None, Hard, Soft) |
| `shadowResolution` | Property | Shadow map quality |
| `shadowBias` / `shadowNormalBias` | Property | Shadow artifact reduction |
| `bounceIntensity` | Property | GI bounce strength |
| `cookie` | Property | Projected texture mask |
| `cullingMask` | Property | Layer-based filtering |
| `colorTemperature` | Property | CCT in Kelvin |
| `lightmapBakeType` | Property | Baking configuration |
| `bakingOutput` | Property | Last bake contribution details |
| `AddCommandBuffer()` | Method | Execute GPU commands at specified points |

### ParticleSystem (UnityEngine.ParticleSystem)
| Member | Type | Description |
|--------|------|-------------|
| `main` / `emission` / `shape` | Property | Module access structs |
| `particleCount` | Property | Current active particles |
| `isPlaying` / `isPaused` / `isStopped` | Property | Playback state |
| `Play()` / `Pause()` / `Stop()` | Method | Playback control |
| `Emit(count)` | Method | Immediate particle spawn |
| `Simulate(time)` | Method | Fast-forward simulation |
| `GetParticles()` / `SetParticles()` | Method | Direct particle data access |
| `Clear()` | Method | Remove all particles |
| `TriggerSubEmitter()` | Method | Activate sub-emitters |

### VisualEffect (UnityEngine.VFX.VisualEffect)
| Member | Type | Description |
|--------|------|-------------|
| `visualEffectAsset` | Property | Assign/change effect graph |
| `playRate` | Property | Simulation speed |
| `aliveParticleCount` | Property | Active particle count |
| `Play()` / `Stop()` / `Reinit()` | Method | Playback control |
| `SendEvent(name, attr)` | Method | Trigger graph events |
| `CreateVFXEventAttribute()` | Method | Create event payload |
| `SetFloat()` / `SetVector3()` / etc. | Method | Set exposed properties |
| `GetFloat()` / `GetVector3()` / etc. | Method | Read exposed properties |
| `HasFloat()` / `HasVector3()` / etc. | Method | Check property existence |
| `ResetOverride(property)` | Method | Restore original values |

### ReflectionProbe (UnityEngine.ReflectionProbe)
| Member | Type | Description |
|--------|------|-------------|
| `mode` | Property | Baked/Custom/Realtime |
| `size` / `center` | Property | Bounding box config |
| `intensity` / `importance` | Property | Brightness and priority |
| `boxProjection` | Property | Enable box projection |
| `refreshMode` / `timeSlicingMode` | Property | Realtime update config |
| `RenderProbe()` | Method | Force cubemap refresh |
| `IsFinishedRendering()` | Method | Check time-sliced completion |
| `BlendCubemap()` | Method | Blend two cubemaps |

## Related Skills
- `unity-graphics` -- Render pipelines (URP/HDRP/Built-in), shaders, materials, cameras
- `unity-2d` -- 2D lighting (URP 2D Renderer), sprite rendering
- `unity-platforms` -- Platform-specific lighting quality tiers, mobile optimization

## Additional Resources
- [Lighting Overview](https://docs.unity3d.com/6000.3/Documentation/Manual/LightingOverview.html)
- [Light Types](https://docs.unity3d.com/6000.3/Documentation/Manual/LightTypes.html)
- [Light Modes](https://docs.unity3d.com/6000.3/Documentation/Manual/LightModes-introduction.html)
- [Light Probes](https://docs.unity3d.com/6000.3/Documentation/Manual/LightProbes.html)
- [Reflection Probes](https://docs.unity3d.com/6000.3/Documentation/Manual/ReflectionProbes.html)
- [Adaptive Probe Volumes (URP)](https://docs.unity3d.com/6000.3/Documentation/Manual/urp/probevolumes.html)
- [Particle System Modules](https://docs.unity3d.com/6000.3/Documentation/Manual/configuring-particles.html)
- [VFX Graph Package](https://docs.unity3d.com/Packages/com.unity.visualeffectgraph@17.0/manual/index.html)
- [Light Scripting API](https://docs.unity3d.com/6000.3/Documentation/ScriptReference/Light.html)
- [ParticleSystem Scripting API](https://docs.unity3d.com/6000.3/Documentation/ScriptReference/ParticleSystem.html)
- [ReflectionProbe Scripting API](https://docs.unity3d.com/6000.3/Documentation/ScriptReference/ReflectionProbe.html)

**Agent (2026-11-26 02:22 UTC):**

> _tool: Skill_

### Message (2026-11-26 02:22 UTC)

Base directory for this skill: C:\Users\josia\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\rpm\68d4646f\243b2244\plugin_012dAT1EB1GCjar34htA97xJ\skills\urp-postprocessing

Help the user set up, configure, and debug post-processing effects using URP's Volume framework.

**Goal: The user should have a working visual result with zero console errors after setup.**

## 0. Prerequisite: an Editor you can run C# in

Volume profiles, `VolumeParameter.overrideState`, and the camera's post-processing flags are
Editor/runtime object state — the checks and edits below all run C# inside a live Editor.

**The `unity-cli` skill owns getting you there** — installing the CLI, confirming a connected
Editor, adding the project's `com.unity.pipeline` package, telling a genuinely absent Editor
apart from one stuck in Safe Mode, and discovering the Editor's command catalog. Follow it
first; don't re-derive any of it here. You need `script eval` in particular, not just a reachable
Editor: its presence depends on the Pipeline package version, not on the CLI. If it's
missing, say so and stop.

Run C# through the connected Editor with the `script eval` command. Discover its parameter shape
from `unity command --format json` rather than assuming one — the inline form is
`unity command script eval --caller plugin --skill urp-postprocessing --code '<snippet>'`, and some Pipeline versions also register
`script eval_file` for running a snippet from a file. **Check the catalog before reaching for
`script eval_file`; it is frequently absent.** `unity command` defaults to a 30 second timeout.

### Passing C# to `script eval`

`script eval` compiles a **statement block, not a file**. Two consequences, both of which cause a
compile error rather than a warning:

- **No `using` directives.** The compiler reads `using UnityEngine;` as a resource-disposal
  statement and rejects it (`CS0210`).
- **Types must be fully qualified.** A bare `AssetDatabase` or `Volume` does not resolve
  (`CS0246` / `CS0103`), and a bare `Object` is ambiguous with `object` (`CS0104`).

Where a snippet below is written as a file — with usings, for readability, or because it is
meant to be saved into the project — qualify the types before passing it to `script eval`.

## 0. Pre-Flight Checks

Before configuring any effect, **verify all checks**. Fix failures first.

1. **URP is the active render pipeline** — If not, inform the user and stop.
2. **HDR is enabled on the URP Asset** — Required for Tonemapping. Bloom works best with HDR; in SDR it still works but `threshold` must be < 1.
3. **Camera has post-processing enabled** — `renderPostProcessing` must be `true` (defaults to `false`). Camera Stacking: only a `CameraRenderType.Base` camera (or the last `Overlay` in the stack) should enable post-processing. Also verify the Renderer's PostProcessData asset is not null — if it is, the post-process pass won't exist.
4. **The Volume's GameObject layer is in the Camera's Volume Layer Mask** — `volumeLayerMask` defaults to layer 0 "Default" only. The Volume's `GameObject.layer` must be included, otherwise the camera ignores it.
5. **Volume exists with `enabled = true`, a valid Profile, and at least one override** — The `Volume` component must be enabled, have a non-null `profile` (or `sharedProfile`), and at least one `VolumeComponent` with `overrideState = true` on its properties.

### Pre-Flight Check Snippet

Run this to verify the setup programmatically:

```csharp
// `script eval` compiles a statement block, not a file: no `using` directives are
// allowed, so every type is fully qualified.
var report = new System.Text.StringBuilder();

// 1. Check URP is active — a hard stop, so throw: it fails the eval loudly
var urpAsset = UnityEngine.Rendering.Universal.UniversalRenderPipeline.asset;
if (urpAsset == null)
    throw new System.Exception("URP is not the active render pipeline.");

// 2. Check HDR
if (!urpAsset.supportsHDR)
    report.AppendLine("Warning: HDR is disabled on the URP Asset. Tonemapping won't work; Bloom requires threshold < 1.");

// 3. Check camera post-processing
var cam = UnityEngine.Camera.main;
if (cam == null)
    throw new System.Exception("No Main Camera found.");
if (!cam.TryGetComponent<UnityEngine.Rendering.Universal.UniversalAdditionalCameraData>(out var camData))
    throw new System.Exception("Missing UniversalAdditionalCameraData on camera. Is URP active?");
if (!camData.renderPostProcessing)
    report.AppendLine("Warning: Post-processing is disabled on the camera. Enable via camData.renderPostProcessing = true.");

// 4. Check volume layer mask
var volumes = UnityEngine.Object.FindObjectsByType<UnityEngine.Rendering.Volume>(UnityEngine.FindObjectsSortMode.None);
foreach (var vol in volumes)
{
    if (!vol.enabled) { report.AppendLine($"Warning: Volume '{vol.name}' is disabled."); continue; }
    if ((camData.volumeLayerMask & (1 << vol.gameObject.layer)) == 0)
        report.AppendLine($"Warning: Volume '{vol.name}' on layer {vol.gameObject.layer} is not in camera's volumeLayerMask.");
    // 5. Check profile and overrides
    var profile = vol.sharedProfile;
    if (profile == null) { report.AppendLine($"Warning: Volume '{vol.name}' has no profile assigned."); continue; }
    if (profile.components.Count == 0)
        report.AppendLine($"Warning: Volume '{vol.name}' profile has no overrides.");
}

// Return the findings: logs land in the Editor console, the returned value comes back to you
return report.Length == 0 ? "Post-processing setup looks correct." : report.ToString();
```

## 1. Volume Setup

Effects are added as **VolumeComponent overrides** on a **VolumeProfile** (a `ScriptableObject`).

**Global Volume** (most common): GameObject with `Volume` component, `isGlobal = true`, `profile` assigned. Affects every camera whose `volumeLayerMask` includes the Volume's layer.

**Local Volume (optional, but takes precedence)**: GameObject with trigger `Collider` + `Volume` component, `isGlobal = false`. Properties:
- `priority` (float) — higher values override lower when volumes overlap.
- `blendDistance` (float) — outer distance in world units to start blending from (0 = no blend, instant transition at collider boundary).
- `weight` (float, 0–1) — scales the volume's overall influence.

## 2. Post-Processing Effects

All effects are `VolumeComponent` subclasses added as overrides on a `VolumeProfile` via `profile.Add<T>()`. Check existence with `profile.Has<T>()` or `profile.TryGet<T>(out var t)`. Remove with `profile.Remove<T>()`.

Every property is a `VolumeParameter`. You **must** set `overrideState = true` before setting `value`, otherwise the Volume system ignores it.

When configuring a specific effect, load the full API reference:
- [references/effect-reference.md](references/effect-reference.md) — All VolumeComponent properties by effect (Bloom, Tonemapping, ColorAdjustments, DepthOfField, Vignette, MotionBlur, FilmGrain, ChromaticAberration, SplitToning, LensDistortion, WhiteBalance, PaniniProjection, LiftGammaGain, ShadowsMidtonesHighlights, ColorCurves, ChannelMixer)

For code templates:
- [references/code-templates.md](references/code-templates.md) — Global Volume setup, camera post-processing, and profile modification templates

## 3. Anti-Hallucination Rules

### Required Usings

These apply when you write a `.cs` file into the project. **A snippet passed to `script eval` cannot
carry them** — qualify the types instead (see "Passing C# to `script eval`" above).

```csharp
using UnityEngine.Rendering;           // Volume, VolumeProfile, VolumeComponent, VolumeParameter
using UnityEngine.Rendering.Universal;  // Bloom, Tonemapping, ColorAdjustments, UniversalRenderPipeline, etc.
```

### Wrong → Correct API Mapping

| WRONG | CORRECT |
|-------|---------|
| `PostProcessVolume` | `Volume` (from `UnityEngine.Rendering`) |
| `PostProcessLayer` | `UniversalAdditionalCameraData.renderPostProcessing` (bool) |
| `UnityEngine.Rendering.PostProcessing` | `UnityEngine.Rendering.Universal` |
| `profile.GetSetting<T>()` | `profile.TryGet<T>(out var t)` (returns bool) |
| `profile.AddSettings<T>()` | `profile.Add<T>()` (returns T; throws if already exists — check `profile.Has<T>()` first) |
| `volume.sharedProfile` (to modify at runtime) | `volume.profile` (auto-clones the asset into an instance) |
| `VolumeManager.instance.stack.GetComponent<T>()` | `volume.profile.TryGet<T>(out var t)` |

### Key Facts
- **`overrideState = true`** is required on every `VolumeParameter` you set. The volume system skips parameters where `overrideState` is `false`. This is the #1 scripting mistake.
- **`sharedProfile`** = returns the asset directly (edits persist to disk). **`profile`** = auto-clones into an instance if needed (safe for runtime edits). Check with `volume.HasInstantiatedProfile()`.
- **`profile.Add<T>(bool overrides = false)`** — pass `true` to auto-enable `overrideState` on all parameters of the added component.

## 4. Debugging Checklist

When post-processing isn't working, check in order:

1. `cam.TryGetComponent<UniversalAdditionalCameraData>(out var data)` succeeds and `data.renderPostProcessing` is `true`?
2. Volume exists in scene with a non-null `profile` (or `sharedProfile`) assigned?
3. Overrides added via `profile.Add<T>()` AND `overrideState = true` on each property you set?
4. Volume's `GameObject.layer` is included in camera's `data.volumeLayerMask`? (Default mask is layer 0 "Default" only.)
5. `volume.isGlobal = true` (for global), or camera is inside the Volume's trigger `Collider` (for local)?
6. Camera `data.renderType` is `CameraRenderType.Base`, not `Overlay`? (Overlay cameras composite onto the Base camera's output.)
7. `UniversalRenderPipeline.asset.supportsHDR` is `true`? Required for Bloom and Tonemapping.
8. Viewing in **Game view**? Scene view has a separate post-processing toggle in its toolbar.

## 5. Common Recipes

Format: Effect property=value. Bloom values are threshold/intensity/scatter.

**Cinematic (Film):** Tonemapping mode=ACES, ColorAdjustments contrast=15 saturation=-10, Bloom threshold=0.9 intensity=0.5 scatter=0.7, Vignette intensity=0.3 smoothness=0.4, FilmGrain type=Medium1 intensity=0.2

**Stylized/Vibrant:** Tonemapping mode=Neutral, ColorAdjustments saturation=20 contrast=10, Bloom threshold=0.8 intensity=1.5 scatter=0.6, SplitToning highlights=warm shadows=cool

**Horror/Dark:** ColorAdjustments postExposure=-0.5 saturation=-30 contrast=20, Vignette intensity=0.5 smoothness=0.3 color=dark-red, FilmGrain type=Large01 intensity=0.4, ChromaticAberration intensity=0.15

**Clean/Mobile:** Tonemapping mode=Neutral, ColorAdjustments postExposure=0.2, Bloom threshold=1.0 intensity=0.3 (subtle). Avoid FilmGrain, MotionBlur, DepthOfField on mobile.

## 6. Final Confirmation

After setup, report to user:

```
Post-Processing Setup Complete
- Volume: [Global/Local] on "[GameObject Name]"
- Profile: [Asset Path]
- Effects: [List with key property=value pairs]
- Camera: [Name] — renderPostProcessing=true, volumeLayerMask includes layer [N]

View results in Game view (not Scene view).
Undo all changes with Edit > Undo (Ctrl+Z).
```

**Agent (2026-11-26 02:22 UTC):**

> _tool: Bash - Check camera post settings and default volume profile_

**Agent (2026-11-26 02:22 UTC):**

> _tool: Bash - Read camera creation code_

**Agent (2026-11-26 02:23 UTC):**

> _tool: Bash - Read drum wall shader_

**Agent (2026-11-26 02:23 UTC):**

> _tool: Bash - Find scene builder constants_

**Agent (2026-11-26 02:23 UTC):**

> _tool: Bash - Read scene build main flow and knots_

**Agent (2026-11-26 02:23 UTC):**

> _tool: Bash - Find hero shot distance in logs_

**Agent (2026-11-26 02:23 UTC):**

> _tool: Bash - List Unity managed DLLs and xml docs_

**Agent (2026-11-26 02:23 UTC):**

> _tool: Bash - List RenderSettings API members from docs xml_

**Agent (2026-11-26 02:23 UTC):**

> _tool: Bash - Check customReflection and ReflectionProbe API docs_

**Agent (2026-11-26 02:24 UTC):**

> _tool: Read - C:\Users\josia\thanksgiving\Captures\agents\_lead_test\hero_9x16.png_

**Agent (2026-11-26 02:24 UTC):**

> _tool: Bash - Check Python with PIL and numpy_

**Agent (2026-11-26 02:24 UTC):**

> _tool: Write - C:\Users\josia\AppData\Local\Temp\claude\5d9ef3fae1e6adff\b3410996-81ad-4e2d-9d43-bf3d56c2a918\scratchpad\imgstats.ps1_

**Agent (2026-11-26 02:25 UTC):**

> _tool: PowerShell - Compute color stats for reference vs current render_

**Agent (2026-11-26 02:25 UTC):**

> _tool: Bash - Read rest of ProjectSetup_

**Agent (2026-11-26 02:26 UTC):**

> _tool: Bash - Read fur and character shader fragment code_

**Agent (2026-11-26 02:26 UTC):**

> _tool: Bash - List Blender scripts and previews_

**Agent (2026-11-26 02:26 UTC):**

> _tool: Bash - Find bulb, ring, star, coin builders_

**Agent (2026-11-26 02:26 UTC):**

> _tool: Bash - Read ring, bulb and neon star geometry builders_

**Agent (2026-11-26 02:27 UTC):**

> _tool: Bash - Inspect URP Bloom override parameters_

### Message (2026-11-26 02:27 UTC)

[Request interrupted by user]

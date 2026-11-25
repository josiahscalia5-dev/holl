# Bubble Wash Kingdom — 3D asset spec (Blender -> Unity)

All art is built by deterministic Blender 5.3 Python scripts (one per asset group) in
`Tools/Blender/scripts/`, run headless:

```
"C:\Users\josia\Blender\blender-5.3.0-windows-x64\blender.exe" --background --factory-startup --python Tools/Blender/scripts/<script>.py
```

Look and proportions follow `Reference/VISUAL_ANALYSIS.md` (art bible) and the reference frames in
`Reference/frames/` (rear gameplay view 0.00-3.25 s, tunnel 3.75-15 s).

## Units, axes, pivots
- Meters, scene unit scale 1.0. **1 BW (mascot body width) = 0.85 m.**
- Blender Z is up. The asset's **front / direction of travel faces Blender -Y**; its right side is Blender -X.
  (Unity mapping after import: Unity X = -Blender X, Unity Y = Blender Z, Unity Z = -Blender Y, so front = Unity +Z.)
- Characters: origin at the ground contact point between the feet.
- Track modules (slide, tunnel shell, pipe): straight, running from y = 0 to y = -L (L = 4.0 m), cross-section
  centred on X = 0; the slide floor centre line sits at Z = 0 (the gameplay spline runs along it). At least
  16 evenly spaced edge loops along the length so they bend smoothly. Unity bends them along splines.
- Rings, portholes, stars: origin at their centre, ring/disc plane = Blender XZ (axis along Y, facing the player).
- Floor-standing machinery: origin at base centre. Floating items (coins, gems, socks, bubbles): origin at centre.

## Export (FBX)
```python
bpy.ops.export_scene.fbx(filepath=..., use_selection=True, object_types={'MESH','ARMATURE','EMPTY'},
    apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL', axis_forward='-Z', axis_up='Y',
    bake_space_transform=False, use_mesh_modifiers=True, mesh_smooth_type='FACE', use_tspace=True,
    add_leaf_bones=False, primary_bone_axis='Y', secondary_bone_axis='X', use_armature_deform_only=True,
    bake_anim=<True only for the mascot>, bake_anim_use_all_actions=True, bake_anim_use_nla_strips=False,
    bake_anim_force_startend_keying=True, bake_anim_simplify_factor=0.0, path_mode='AUTO', embed_textures=False)
```
- Apply all object transforms (rotation/scale) before export; keep modifiers that matter applied/exported.
- Unity imports with `bakeAxisConversion = true` and remaps materials **by slot name**, so slot names below are a contract.
- Output: `Assets/BubbleWashKingdom/Art/Models/<Group>/<AssetName>.fbx`. Name objects `SM_*` (static) / `SK_*` (skinned).

## Materials (slot names are the contract)
Give each slot a Principled BSDF with the art-bible colour so previews read correctly; Unity replaces it.
| Slot | Used for |
|---|---|
| `M_Fur` | mascot body fur (shells), tail |
| `M_PomPom` | beanie pom-pom fur |
| `M_EyeIris` | big glossy brown eyes |
| `M_EyeHighlight` | white catchlight discs (2 per eye) |
| `M_Mouth`, `M_Tongue` | open smile interior, tongue |
| `M_PawPad` | white/light-pink sole pads and toe beans, palm pads |
| `M_HatKnit` | beanie dome (stripes come from UV v in the shader) |
| `M_HatCuff` | ribbed folded cuff |
| `M_HatStripe` | light stripe band(s) |
| `M_StarBadge` | yellow star badge |
| `M_Water` | flowing water surface of the slide channel |
| `M_SlideShell` | slide outer/under shell |
| `M_RailPink` | glossy pink rails |
| `M_RailRainbow` | rainbow bands on the rail inner faces |
| `M_DrumWall` | perforated purple metallic wall (holes come from the shader, UV u = around, v = along) |
| `M_Gold` / `M_GoldDark` | polished gold / recessed gold details |
| `M_Bulb` | warm marquee bulbs (emissive) |
| `M_Neon` | neon star tubes (colour set per instance in Unity) |
| `M_Glass` | transparent pipes, porthole glass |
| `M_PipeWater` | glowing liquid core in pipes |
| `M_ChamberSwirl` | swirling rainbow water disc/volume in side chambers |
| `M_BrushPink` / `M_BrushBlue` / `M_BrushWhite` | fluffy roller layers |
| `M_MachinePink` / `M_MachineLavender` / `M_PlasticWhite` / `M_MetalPurple` | machinery bodies |
| `M_Screen` / `M_ButtonCyan` / `M_ButtonYellow` / `M_ButtonPink` | control panel details |
| `M_Coin` | gold coin (paw emblem is real geometry) |
| `M_Gem` | purple faceted gem |
| `M_Arrow` / `M_ArrowRim` | glowing cyan chevron / white rim |
| `M_Fabric` | socks, towels, shirts (stripe colours in vertex colour attribute `Col`) |
| `M_Foam` | white foam clumps |
| `M_Bubble` | soap bubble |

## UVs and attributes
- Every mesh has UV map `UVMap` (UV0). Use purpose-built UVs where the shader needs them: drum wall
  (u around circumference, v along length in meters/4), slide water (u across 0..1, v along length/4),
  rails (u around tube, v along), beanie (u around, v bottom->top 0..1), fur (spherical), brush layers (u around).
- Mascot fur shells: second UV map `ShellUV` with u = shell fraction (0 = skin, 1 = tip), v = fur-length mask.
- Optional colour attribute `Col` (byte colour, corner domain) for stripes/tints.

## Triangle budgets (mobile)
Mascot total with shells <= 55k (base body <= 4k before shells, 12-14 shells); eyes+mouth <= 1.5k; beanie <= 5k.
Coin <= 900, gem <= 300, chevron <= 300, neon star <= 1.5k, bulb <= 100, ring <= 4k, slide module <= 3k,
tunnel module <= 3k, pipe module <= 800, porthole + chamber <= 8k, brush roller <= 10k, control panel <= 6k,
agitator <= 4k, sock/towel/shirt <= 800, foam clump <= 1.5k.

## Preview renders
Each script renders `Docs/AssetPreviews/<AssetName>.png` (1000x1000, or 1280x720 for wide sets) with EEVEE
(fallback Cycles 32 samples), view transform `Standard`, warm key + cool fill + pink rim, background #2A1B4A.
Show the asset from the angle the player sees it (from behind/above for the mascot, plus a front view).

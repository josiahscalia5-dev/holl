// Purple metallic washing-machine drum wall, fully procedural (no textures, mobile friendly: one pass + shadow caster).
//  _Pattern 0: staggered grid of round / stretched perforations with bevelled rims (hall, flat bulkheads).
//  _Pattern 1: drum sections between the lavender rims / gold rings placed every _BandLength m from _BandOffset
//              (SceneBuilder.BuildRings): plain metal with two pressed grooves next to every rim, rows of capsule slots
//              elongated around the drum (length varies per row, staggered), countersunk lips, deep hole interiors with a
//              few holes lit from behind, panel seams, twinkling metal sparkles and a lavender grazing sheen that brightens
//              the far tunnel (reference f_003.00s / key 5.0 s).
// UV0.x wraps around the circumference (0..1, 0 = floor, 0.5 = ceiling), UV0.y = distance along the tunnel / _VTile.
Shader "BWK/DrumWall"
{
    Properties
    {
        _BaseColor ("Metal Color", Color) = (0.48, 0.30, 0.82, 1)
        _HighlightColor ("Highlight Color", Color) = (0.78, 0.62, 1.0, 1)
        _HoleColor ("Hole Color", Color) = (0.07, 0.03, 0.16, 1)
        _HoleGlow ("Hole Inner Glow", Color) = (0.45, 0.25, 0.9, 1)
        _Circumference ("Circumference (m)", Float) = 31.4
        _VTile ("Meters per V", Float) = 4
        _HoleSpacing ("Hole Spacing (m)", Float) = 0.42
        _HoleRadius ("Hole Radius (fraction of cell)", Range(0.05, 0.45)) = 0.26
        _Bevel ("Rim Bevel", Range(0, 1)) = 0.6
        _PanelLength ("Panel Length (m)", Float) = 3.0
        _Metallic ("Metallic", Range(0,1)) = 0.75
        _Smoothness ("Smoothness", Range(0,1)) = 0.72
        _Glow ("Self Glow", Range(0,1)) = 0.12
        _HoleBand ("Perforated band (0..1 of circumference, centred on the ceiling)", Range(0,1)) = 1
        _HoleStretch ("Slot elongation around the drum", Range(1, 2.2)) = 1
        [Header(Drum sections)]
        _Pattern ("Pattern (0 grid, 1 drum sections)", Float) = 0
        _BandLength ("Section length (m)", Float) = 2.8333
        _BandOffset ("First rim distance (m)", Float) = 65
        _PlainBack ("Plain metal after a rim (m)", Float) = 0.5
        _PlainFront ("Plain metal before a rim (m)", Float) = 0.4
        _Rows ("Slot rows per section", Float) = 4
        _SlotPitch ("Slot pitch around (m)", Float) = 0.5
        _SlotLength ("Slot length (m)", Float) = 0.34
        _SlotWidth ("Slot width (m)", Float) = 0.12
        _SlotVariation ("Slot length variation", Range(0,1)) = 0.4
        _LipWidth ("Countersink lip width (m)", Float) = 0.035
        _GlowChance ("Glowing hole fraction", Range(0,0.5)) = 0.07
        [HDR] _GlowColorA ("Glowing hole A", Color) = (1.6, 0.8, 1.5, 1)
        [HDR] _GlowColorB ("Glowing hole B", Color) = (0.6, 1.3, 1.8, 1)
        _SeamColor ("Seam / groove color", Color) = (0.2, 0.1, 0.4, 1)
        _SheenColor ("Grazing sheen color", Color) = (0.85, 0.75, 1, 1)
        _SheenStrength ("Grazing sheen", Range(0,2)) = 0
        _Sparkle ("Metal sparkles", Range(0,3)) = 0
        _CeilingLight ("Ceiling brightening", Range(0,1)) = 0
        _EdgeAO ("Section edge occlusion (next to the rims)", Range(0,1)) = 0
        _EdgeAOWidth ("Section edge occlusion width (m)", Float) = 0.45
        _HoleAO ("Darkening halo around holes", Range(0,1)) = 0
        _HoleAOWidth ("Hole halo width (m)", Float) = 0.07
    }
    SubShader
    {
        Tags { "RenderType"="Opaque" "RenderPipeline"="UniversalPipeline" "Queue"="Geometry" }
        HLSLINCLUDE
        #include "BWKCommon.hlsl"
        CBUFFER_START(UnityPerMaterial)
            half4 _BaseColor, _HighlightColor, _HoleColor, _HoleGlow, _GlowColorA, _GlowColorB, _SeamColor, _SheenColor;
            float _Circumference, _VTile, _HoleSpacing, _HoleRadius, _Bevel, _PanelLength;
            half _Metallic, _Smoothness, _Glow, _HoleBand, _HoleStretch;
            float _Pattern, _BandLength, _BandOffset, _PlainBack, _PlainFront, _Rows, _SlotPitch, _SlotLength, _SlotWidth;
            float _SlotVariation, _LipWidth;
            half _GlowChance, _SheenStrength, _Sparkle, _CeilingLight, _EdgeAO, _HoleAO;
            float _EdgeAOWidth, _HoleAOWidth;
        CBUFFER_END
        ENDHLSL

        Pass
        {
            Name "ForwardLit"
            Tags { "LightMode"="UniversalForward" }
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE
            #pragma multi_compile_fragment _ _SHADOWS_SOFT _SHADOWS_SOFT_LOW _SHADOWS_SOFT_MEDIUM _SHADOWS_SOFT_HIGH
            #pragma multi_compile _ _ADDITIONAL_LIGHTS_VERTEX _ADDITIONAL_LIGHTS
            #pragma multi_compile_fragment _ _REFLECTION_PROBE_BLENDING
            #pragma multi_compile_fragment _ _REFLECTION_PROBE_BOX_PROJECTION
            #pragma multi_compile_fog
            #pragma multi_compile_instancing

            struct Attributes { float4 positionOS : POSITION; float3 normalOS : NORMAL; float4 tangentOS : TANGENT; float2 uv : TEXCOORD0; UNITY_VERTEX_INPUT_INSTANCE_ID };
            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float3 positionWS : TEXCOORD0;
                half3 normalWS : TEXCOORD1;
                half4 tangentWS : TEXCOORD2;
                float2 uv : TEXCOORD3;
                half fog : TEXCOORD4;
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };

            Varyings vert(Attributes i)
            {
                Varyings o = (Varyings)0;
                UNITY_SETUP_INSTANCE_ID(i);
                UNITY_TRANSFER_INSTANCE_ID(i, o);
                VertexPositionInputs p = GetVertexPositionInputs(i.positionOS.xyz);
                VertexNormalInputs n = GetVertexNormalInputs(i.normalOS, i.tangentOS);
                o.positionCS = p.positionCS;
                o.positionWS = p.positionWS;
                o.normalWS = n.normalWS;
                o.tangentWS = half4(n.tangentWS, i.tangentOS.w * GetOddNegativeScale());
                o.uv = i.uv;
                o.fog = ComputeFogFactor(p.positionCS.z);
                return o;
            }

            half4 frag(Varyings i) : SV_Target
            {
                float2 m = float2(i.uv.x * _Circumference, i.uv.y * _VTile);     // (around, along) in meters
                float around = abs(frac(i.uv.x) - 0.5) * 2.0;                     // 0 = ceiling, 1 = floor
                float band = step(around, _HoleBand + 1e-3);                       // perforated band around the ceiling
                half3 bitangent = cross(i.normalWS, i.tangentWS.xyz) * i.tangentWS.w;

                float hole = 0.0, lip = 0.0, inner = 0.0, glowSel = 0.0, groove = 0.0, detail = 1.0, ao = 1.0;
                float2 dir = float2(0.0, 0.0);
                half3 glowCol = half3(0.0, 0.0, 0.0);

                if (_Pattern < 0.5)
                {
                    float2 cell = m / _HoleSpacing;
                    float row = floor(cell.y);
                    cell.x += fmod(abs(row), 2.0) * 0.5;                           // staggered rows
                    float2 local = frac(cell) - 0.5;
                    float dist = length(float2(local.x / _HoleStretch, local.y));
                    float r = _HoleRadius;
                    float aa = fwidth(dist) * 1.5 + 1e-4;
                    hole = (1.0 - smoothstep(r - aa, r + aa, dist)) * band;
                    lip = smoothstep(r + 0.12, r, dist) * (1.0 - hole) * band;
                    dir = dist > 1e-4 ? -local / dist : float2(0.0, 0.0);         // rim pushed outward (raised)
                    inner = saturate(1.0 - dist / max(r, 1e-3));
                    float seamD = abs(frac(m.y / _PanelLength) - 0.5) * 2.0;
                    groove = smoothstep(0.985, 0.995, seamD) * 0.6;
                }
                else
                {
                    float L = max(_BandLength, 0.5);
                    float bandF = (m.y - _BandOffset) / L;
                    float bandIdx = floor(bandF);
                    float local = (bandF - bandIdx) * L;                           // meters after the last rim
                    float z0 = _PlainBack;
                    float zoneLen = max(L - _PlainFront - z0, 0.2);
                    float rows = max(1.0, _Rows);
                    float rowPitch = zoneLen / rows;
                    float rowIdx = clamp(floor((local - z0) / rowPitch), 0.0, rows - 1.0);
                    float rowLocal = local - z0 - (rowIdx + 0.5) * rowPitch;       // meters from the nearest row centre
                    float rowHash = BWK_Hash21(float2(rowIdx + 0.5, bandIdx + 0.25));
                    float slotLen = _SlotLength * lerp(1.0 - _SlotVariation, 1.0 + _SlotVariation * 0.5, rowHash);
                    float stagger = frac((rowIdx + bandIdx) * 0.5);                  // 0 / 0.5 alternating rows
                    float ac = m.x / _SlotPitch + stagger;
                    float slotIdx = floor(ac);
                    float aLocal = (ac - slotIdx - 0.5) * _SlotPitch;
                    float hw = _SlotWidth * 0.5;
                    float hx = max(abs(aLocal) - max(slotLen * 0.5 - hw, 0.0), 0.0);
                    float2 q = float2(hx * sign(aLocal), rowLocal);
                    float ql = length(q);
                    float sdf = ql - hw;                                            // capsule distance (m), < 0 inside
                    float aa = fwidth(sdf) * 1.2 + 1e-4;
                    // fade the perforation out where a slot gets thinner than ~1.5 px (no shimmer far down the tunnel)
                    float px = max(fwidth(m.x), fwidth(m.y));
                    detail = saturate((hw / max(px, 1e-5) - 0.75) * 0.8);
                    hole = (1.0 - smoothstep(-aa, aa, sdf)) * band * detail;
                    lip = (1.0 - smoothstep(0.0, _LipWidth, sdf)) * (1.0 - hole) * band * detail;
                    dir = ql > 1e-5 ? q / ql : float2(0.0, 0.0);                    // countersunk: sloping into the hole
                    inner = saturate(-sdf / hw);
                    float hId = BWK_Hash21(float2(slotIdx * 0.37 + rowIdx * 3.1, bandIdx * 1.7 + 0.5));
                    glowSel = step(hId, _GlowChance) * band;
                    glowCol = lerp(_GlowColorA.rgb, _GlowColorB.rgb, step(0.5, frac(hId * 31.7)));
                    // two pressed grooves in the plain metal next to every rim + longitudinal panel seams (8 around)
                    float ga = fwidth(local) * 1.5 + 0.004;
                    float gA = abs(local - (z0 - 0.17));
                    float gB = abs(local - (L - _PlainFront + 0.15));
                    groove = max(1.0 - smoothstep(0.007, 0.007 + ga, gA), 1.0 - smoothstep(0.007, 0.007 + ga, gB));
                    float seamW = fwidth(m.x) * 1.5 + 0.006;
                    float seamX = abs(frac(m.x / (_Circumference / 8.0) + 0.5) - 0.5) * (_Circumference / 8.0);
                    groove = max(groove, (1.0 - smoothstep(0.006, 0.006 + seamW, seamX)) * 0.65);
                    // ambient occlusion: the drum section is darker where it meets the raised rims / gold rings and in
                    // a soft halo around every perforation (reference f_003.00s: dark values around the holes)
                    float eW = max(_EdgeAOWidth, 1e-3);
                    float edge = smoothstep(0.0, eW, local) * smoothstep(0.0, eW, L - local);
                    float halo = smoothstep(_HoleAOWidth + 0.01, 0.0, sdf) * (1.0 - hole) * band * detail;
                    ao = lerp(1.0 - _EdgeAO, 1.0, edge) * (1.0 - _HoleAO * halo);
                }

                // countersink / bevel normal (dir points from the hole centre line outward, in (around, along))
                half3 n = normalize(i.normalWS - (i.tangentWS.xyz * dir.x + bitangent * dir.y) * lip * _Bevel);

                float variation = BWK_Fbm(m * 0.35);
                half3 metal = lerp(_BaseColor.rgb, _HighlightColor.rgb, saturate(variation * 0.55 + lip * 0.45));
                metal *= 1.0 + _CeilingLight * (1.0 - around);
                metal *= 1.0 - (1.0 - detail) * 0.12 * band * step(0.5, _Pattern);   // far: average in the hole darkness
                metal = lerp(metal, _SeamColor.rgb, saturate(groove) * 0.75);
                metal *= ao;
                half depthT = smoothstep(0.0, 0.7, inner);
                half3 holeCol = lerp(_HoleColor.rgb * 1.8 + _HoleGlow.rgb * 0.12, _HoleColor.rgb * 0.35, depthT);
                half3 albedo = lerp(metal, holeCol, hole);
                half metallic = lerp(_Metallic, 0.0, hole);
                half smooth = lerp(_Smoothness, 0.25, hole);

                half3 viewDir = GetWorldSpaceNormalizeViewDir(i.positionWS);
                half fres = BWK_Fresnel(n, viewDir, 3.0);
                half3 emission = metal * _Glow * (1.0 - hole)
                               + _HoleGlow.rgb * hole * (1.0 - depthT) * 0.5
                               + _SheenColor.rgb * fres * _SheenStrength * (1.0 - hole);
                // a few holes lit from behind (light leaking through the drum)
                half flicker = 0.8 + 0.2 * sin(_Time.y * 2.3 + m.x * 1.7 + m.y * 0.9);
                emission += glowCol * hole * glowSel * (0.35 + 0.65 * depthT) * flicker;
                // twinkling sparkles on the polished metal
                float2 sc = m / 0.27;
                float2 sci = floor(sc);
                float sh = BWK_Hash21(sci + 7.31);
                float2 so = float2(BWK_Hash21(sci + 1.7), BWK_Hash21(sci + 9.2)) - 0.5;
                float sd = length(frac(sc) - 0.5 - so * 0.5);
                half twinkle = saturate(sin(_Time.y * 2.6 + sh * 60.0) * 0.5 + 0.5);
                half spark = step(0.94, sh) * smoothstep(0.16, 0.0, sd) * twinkle * saturate(1.0 - fwidth(sc.x) * 3.0);
                emission += _SheenColor.rgb * spark * _Sparkle * (1.0 - hole);

                return BWK_PBR(i.positionWS, i.positionCS, n, viewDir, albedo, metallic, smooth, lerp(ao, 0.4, hole), emission, 1.0, i.fog);
            }
            ENDHLSL
        }
        Pass
        {
            Name "ShadowCaster"
            Tags { "LightMode"="ShadowCaster" }
            ZWrite On ZTest LEqual ColorMask 0
            HLSLPROGRAM
            #pragma vertex ShadowVert
            #pragma fragment ShadowFrag
            #pragma multi_compile_instancing
            #pragma multi_compile_vertex _ _CASTING_PUNCTUAL_LIGHT_SHADOW
            #include "BWKShadow.hlsl"
            ENDHLSL
        }
    }
    FallBack Off
}

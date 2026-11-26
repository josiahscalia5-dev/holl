// Flowing slide water (reference f_003.00s: bright turquoise-cyan, glossy, translucent and dimensional).
// Layers, bottom to top:
//  - turquoise body: deep blue toward the walls, lighter turquoise centre lane, brighter where the camera looks down into it
//  - subsurface (parallax, _Depth below the surface): a slow caustic light web and soft streaks seen THROUGH the water
//  - cyan light pools around the decor chevrons (same period as SceneBuilder.BuildDecorChevrons, set by MaterialLibrary)
//  - pink / rainbow pickup from the candy banks, white foam lines along the walls
//  - fast thin white speed streaks on the surface, sparkle glints
//  - flowing ripple normals -> glossy URP PBR lighting + boosted probe reflections (tunnel, gold rings, bulbs)
// UV0.x runs across the channel (0..1), UV0.y = track distance / _VTile (written by SplineMeshDeformer).
Shader "BWK/Water"
{
    Properties
    {
        _DeepColor ("Deep Color", Color) = (0.12, 0.45, 0.85, 1)
        _ShallowColor ("Shallow Color", Color) = (0.25, 0.85, 0.92, 1)
        _StreakColor ("Streak Color", Color) = (0.92, 0.98, 1.0, 1)
        _EdgeTint ("Rail Tint", Color) = (1.0, 0.45, 0.85, 1)
        _CausticColor ("Caustic Color", Color) = (0.6, 1.0, 1.0, 1)
        _ChevronColor ("Chevron Light Color", Color) = (0.3, 0.95, 1.0, 1)
        _VTile ("Meters per V", Float) = 4
        _Width ("Channel Width (m)", Float) = 4.4
        _FlowSpeed ("Flow Speed (m/s)", Float) = 7
        _StreakDensity ("Streak Density", Float) = 1.6
        _StreakAmount ("Streak Amount", Range(0,1)) = 0.6
        _EdgeFoam ("Edge Foam", Range(0,1)) = 0.8
        _EdgeTintAmount ("Rail Tint Amount", Range(0,1)) = 0.45
        _Smoothness ("Smoothness", Range(0,1)) = 0.93
        _Glow ("Self Glow", Range(0,2)) = 0.35
        _RippleStrength ("Ripple Normal Strength", Range(0,2)) = 0.6
        _WaveHeight ("Wave Height (m)", Float) = 0.025
        _SparkleAmount ("Sparkle Glints", Range(0,3)) = 1
        _RainbowAmount ("Rainbow Sheen near the banks", Range(0,1)) = 0.35
        _CausticAmount ("Subsurface Caustics", Range(0,2)) = 0.6
        _Depth ("Parallax Depth (m)", Range(0,0.6)) = 0.2
        _NearBrighten ("Brighten Toward Camera", Range(0,1)) = 0.5
        _ReflectBoost ("Extra Probe Reflection", Range(0,3)) = 0.8
        _CenterGlow ("Centre Lane Glow", Range(0,1)) = 0.3
        _ChevronStart ("Chevron Start (m)", Float) = 6
        _ChevronSpacing ("Chevron Spacing (m, 0 = off)", Float) = 0
        _ChevronScale ("Chevron Scale", Float) = 1.5
        _ChevronWidth ("Chevron Width Factor", Float) = 1
        _ChevronGlow ("Chevron Light Pool", Range(0,3)) = 1
        _TurquoiseColor ("Turquoise Patch Color", Color) = (0.2, 0.75, 0.87, 1)
        _PatchAmount ("Turquoise Patches", Range(0,1)) = 0
        _DetailStrength ("Detail Ripple Normals", Range(0,2)) = 0
        _ReflectTint ("Probe Reflection Tint", Color) = (1, 1, 1, 1)
    }
    SubShader
    {
        Tags { "RenderType"="Opaque" "RenderPipeline"="UniversalPipeline" "Queue"="Geometry" }
        HLSLINCLUDE
        #include "BWKCommon.hlsl"
        CBUFFER_START(UnityPerMaterial)
            half4 _DeepColor, _ShallowColor, _StreakColor, _EdgeTint, _CausticColor, _ChevronColor;
            float _VTile, _Width, _FlowSpeed, _StreakDensity;
            half _StreakAmount, _EdgeFoam, _EdgeTintAmount, _Smoothness, _Glow, _RippleStrength, _SparkleAmount, _RainbowAmount;
            float _WaveHeight;
            half _CausticAmount, _Depth, _NearBrighten, _ReflectBoost, _CenterGlow;
            float _ChevronStart, _ChevronSpacing, _ChevronScale, _ChevronWidth;
            half _ChevronGlow;
            half4 _TurquoiseColor, _ReflectTint;
            half _PatchAmount, _DetailStrength;
        CBUFFER_END

        // flowing height field: long swells stretched along the flow + a finer, faster chop
        float WaterHeight(float2 m, float t)
        {
            float2 p = float2(m.x * 1.7, (m.y - t * _FlowSpeed) * 0.55);
            float h = BWK_ValueNoise(p) * 0.55 + BWK_ValueNoise(p * float2(2.3, 2.9) + 7.1) * 0.3;
            h += BWK_ValueNoise(float2(m.x * 6.0, (m.y - t * _FlowSpeed * 1.2) * 2.2) + 3.7) * 0.15;
            return h;
        }
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
                float2 meters : TEXCOORD3;
                float2 uv : TEXCOORD4;
                half fog : TEXCOORD5;
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };

            Varyings vert(Attributes i)
            {
                Varyings o = (Varyings)0;
                UNITY_SETUP_INSTANCE_ID(i);
                UNITY_TRANSFER_INSTANCE_ID(i, o);
                float2 m = float2(i.uv.x * _Width, i.uv.y * _VTile);
                float edge = smoothstep(0.0, 0.12, i.uv.x) * smoothstep(1.0, 0.88, i.uv.x);
                float3 pos = i.positionOS.xyz + i.normalOS * (WaterHeight(m, _Time.y) - 0.5) * _WaveHeight * edge;
                VertexPositionInputs p = GetVertexPositionInputs(pos);
                VertexNormalInputs n = GetVertexNormalInputs(i.normalOS, i.tangentOS);
                o.positionCS = p.positionCS;
                o.positionWS = p.positionWS;
                o.normalWS = n.normalWS;
                o.tangentWS = half4(n.tangentWS, i.tangentOS.w * GetOddNegativeScale());
                o.meters = m;
                o.uv = i.uv;
                o.fog = ComputeFogFactor(p.positionCS.z);
                return o;
            }

            float Ridge(float n) { return 1.0 - abs(n * 2.0 - 1.0); }

            // distance to the nearest cell border of an animated Voronoi field (0 on the borders) -> caustic light web
            float VoronoiEdge(float2 p, float t)
            {
                float2 ip = floor(p);
                float2 fp = frac(p);
                float d1 = 8.0, d2 = 8.0;
                [unroll] for (int y = -1; y <= 1; y++)
                {
                    [unroll] for (int x = -1; x <= 1; x++)
                    {
                        float2 g = float2(x, y);
                        float2 h = float2(BWK_Hash21(ip + g), BWK_Hash21(ip + g + 17.31));
                        float2 o = 0.5 + 0.42 * sin(t + 6.2831 * h);
                        float d = length(g + o - fp);
                        if (d < d1) { d2 = d1; d1 = d; }
                        else if (d < d2) { d2 = d; }
                    }
                }
                return d2 - d1;
            }

            half4 frag(Varyings i) : SV_Target
            {
                UNITY_SETUP_INSTANCE_ID(i);
                float t = _Time.y;
                float2 m = i.meters;
                half3 viewDir = GetWorldSpaceNormalizeViewDir(i.positionWS);
                half3 bitangent = cross(i.normalWS, i.tangentWS.xyz) * i.tangentWS.w;

                // ---- flowing ripple normal (finite differences of the height field)
                float e = 0.04;
                float h0 = WaterHeight(m, t);
                float hx = WaterHeight(m + float2(e, 0), t);
                float hy = WaterHeight(m + float2(0, e), t);
                float2 grad = float2(hx - h0, hy - h0) / e * _RippleStrength * 0.1;
                // round 3b: two finer ripple layers scrolling at different speeds / angles (flow-map look, no tiling grid)
                if (_DetailStrength > 0.001)
                {
                    float2 q1 = float2(m.x * 3.7 + m.y * 0.45, (m.y - t * _FlowSpeed * 1.08) * 1.45);
                    float2 q2 = float2(m.x * 5.9 - m.y * 0.35 + 9.3, (m.y - t * _FlowSpeed * 0.86) * 2.3 + 4.1);
                    float d0 = BWK_ValueNoise(q1) + 0.6 * BWK_ValueNoise(q2);
                    float dx = BWK_ValueNoise(q1 + float2(0.08, 0)) + 0.6 * BWK_ValueNoise(q2 + float2(0.08, 0));
                    float dy = BWK_ValueNoise(q1 + float2(0, 0.08)) + 0.6 * BWK_ValueNoise(q2 + float2(0, 0.08));
                    grad += float2(dx - d0, dy - d0) * _DetailStrength;
                }
                half3 n = normalize(i.normalWS - (i.tangentWS.xyz * grad.x + bitangent * grad.y));

                float flowY = m.y - t * _FlowSpeed;
                float across = abs(i.uv.x - 0.5) * 2.0;           // 0 centre, 1 at the water line
                half centre = 1.0 - smoothstep(0.05, 0.85, across);

                // ---- subsurface layer seen through the water (parallax _Depth below the surface)
                half3 vTS = half3(dot(viewDir, i.tangentWS.xyz), dot(viewDir, bitangent), dot(viewDir, i.normalWS));
                float2 md = m - vTS.xy / max(vTS.z, 0.22) * _Depth - grad * 0.35;   // parallax + ripple refraction
                float flowD = md.y - t * _FlowSpeed * 0.55;
                float web = VoronoiEdge(float2(md.x * 1.55, flowD * 0.62), t * 1.3);
                half caustic = smoothstep(0.16, 0.015, web);
                half deepStreak = smoothstep(0.82, 0.97, Ridge(BWK_ValueNoise(float2(md.x * 2.6 * _StreakDensity, flowD * 0.09))));

                // ---- body colour: deep blue at the walls -> turquoise centre, swell variation
                half3 body = lerp(_DeepColor.rgb, _ShallowColor.rgb, saturate(centre * 0.8 + (h0 - 0.5) * 0.7 + 0.12));
                // slow flowing turquoise patches over the deep blue (reference: blue -> turquoise variation, no bands)
                half patch = smoothstep(0.42, 0.85, BWK_ValueNoise(float2(md.x * 0.85 + 3.1, (md.y - t * _FlowSpeed * 0.8) * 0.16))
                                                     * 0.7 + BWK_ValueNoise(float2(md.x * 2.1, flowD * 0.5 + 1.7)) * 0.3);
                body = lerp(body, _TurquoiseColor.rgb, patch * _PatchAmount * (0.35 + 0.65 * centre));
                body += _CausticColor.rgb * (caustic * _CausticAmount + deepStreak * 0.35) * (0.3 + 0.7 * centre) * 0.55;
                // brighter, more translucent where the camera looks down into the water (near the camera)
                half ndv = saturate(dot(n, viewDir));
                body = lerp(body, body * 1.18 + _ShallowColor.rgb * 0.22, smoothstep(0.2, 0.8, ndv) * _NearBrighten);

                // ---- light pools around the glowing decor chevrons (SM_Chevron: apex toward travel, 45-degree arms;
                //      arm centre line from (0, +0.26) to (+-0.52, -0.26) chevron metres, x ChevronScale)
                half chevLight = 0;
                if (_ChevronSpacing > 0.01)
                {
                    float s = _ChevronScale;
                    float ly = m.y - _ChevronStart - round((m.y - _ChevronStart) / _ChevronSpacing) * _ChevronSpacing;
                    float lx = abs(m.x - _Width * 0.5) / max(_ChevronWidth, 0.1);
                    float dv = (ly - (0.26 * s - min(lx, 0.6 * s))) * 0.7071;   // distance from the arm centre line
                    half pool = exp(-dv * dv / (0.035 * s * s)) * smoothstep(0.85 * s, 0.5 * s, lx);
                    half wide = exp(-(ly * ly) / (0.35 * s * s)) * smoothstep(1.3 * s, 0.2 * s, lx);
                    chevLight = (pool * 0.85 + wide * 0.25) * _ChevronGlow;
                }

                // ---- banks: pink / rainbow pickup, white foam lines along the walls
                half3 rainbow = BWK_Rainbow(across * 0.9 + BWK_ValueNoise(float2(m.x * 2.0, flowY * 0.2)) * 0.6 - flowY * 0.015);
                body = lerp(body, _EdgeTint.rgb, smoothstep(0.55, 1.0, across) * _EdgeTintAmount);
                body = lerp(body, rainbow, smoothstep(0.5, 0.97, across) * _RainbowAmount);
                float wob = BWK_ValueNoise(float2(m.x * 7.0, flowY * 0.35 + 3.0));
                half foam = smoothstep(0.84, 0.97, across + (wob - 0.5) * 0.12) * _EdgeFoam;

                // ---- fast thin surface speed streaks (long light lines racing down the slide)
                float sx = m.x * _StreakDensity;
                float sA = Ridge(BWK_ValueNoise(float2(sx * 3.1, flowY * 0.07)));
                float sB = Ridge(BWK_ValueNoise(float2(sx * 7.3 + 5.0, flowY * 0.16 + 2.0)));
                float gate = smoothstep(0.3, 0.7, BWK_ValueNoise(float2(sx * 1.3 + 11.0, flowY * 0.22)));
                half streak = saturate((smoothstep(0.9, 0.985, sA) * 0.85 + smoothstep(0.935, 0.992, sB) * 0.55) * gate) * _StreakAmount;

                half3 albedo = lerp(body, _StreakColor.rgb, saturate(streak + foam));
                half smooth = lerp(_Smoothness, 0.55, saturate(foam + streak * 0.5));

                // ---- emission: self glow of the body, centre lane, chevron light, streaks, sparkle glints
                half3 emission = body * _Glow + _ShallowColor.rgb * centre * _CenterGlow * 0.35;
                emission += _ChevronColor.rgb * chevLight;
                emission += _StreakColor.rgb * streak * 0.35 + _CausticColor.rgb * caustic * _CausticAmount * centre * 0.12;
                float2 sp = float2(m.x * 8.0, flowY * 2.6);
                float2 spc = floor(sp);
                float2 spl = frac(sp) - 0.5 - (float2(BWK_Hash21(spc + 3.3), BWK_Hash21(spc + 7.7)) - 0.5) * 0.6;
                half spark = step(0.94, BWK_Hash21(spc)) * smoothstep(0.13, 0.0, length(spl * float2(1.0, 0.6)));
                emission += _StreakColor.rgb * spark * 2.6 * _SparkleAmount * (1.0 - foam);

                // ---- extra glossy probe reflection (tunnel, rings, bulbs) on top of the PBR reflection
                half fres = BWK_Fresnel(n, viewDir, 4.0);
                half3 refl = GlossyEnvironmentReflection(reflect(-viewDir, n), i.positionWS, 0.06h, 1.0h, GetNormalizedScreenSpaceUV(i.positionCS));
                emission += refl * _ReflectTint.rgb * (0.12 + fres * 0.88) * _ReflectBoost * (1.0 - foam);

                return BWK_PBR(i.positionWS, i.positionCS, n, viewDir, albedo, 0.0, smooth, 1.0, emission, 1.0, i.fog);
            }
            ENDHLSL
        }
    }
    FallBack Off
}

// Flowing slide water: vivid blue with white flow streaks moving down the slide, glossy reflections,
// pink/rainbow tint picked up near the rails, white foam lines at the walls and a gentle surface ripple.
// UV0.x runs across the channel (0..1), UV0.y = track distance / _VTile (written by SplineMeshDeformer).
Shader "BWK/Water"
{
    Properties
    {
        _DeepColor ("Deep Color", Color) = (0.05, 0.38, 1.0, 1)
        _ShallowColor ("Shallow Color", Color) = (0.25, 0.85, 1.0, 1)
        _StreakColor ("Streak Color", Color) = (0.92, 0.98, 1.0, 1)
        _EdgeTint ("Rail Tint", Color) = (1.0, 0.45, 0.85, 1)
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
    }
    SubShader
    {
        Tags { "RenderType"="Opaque" "RenderPipeline"="UniversalPipeline" "Queue"="Geometry" }
        HLSLINCLUDE
        #include "BWKCommon.hlsl"
        CBUFFER_START(UnityPerMaterial)
            half4 _DeepColor, _ShallowColor, _StreakColor, _EdgeTint;
            float _VTile, _Width, _FlowSpeed, _StreakDensity;
            half _StreakAmount, _EdgeFoam, _EdgeTintAmount, _Smoothness, _Glow, _RippleStrength, _SparkleAmount, _RainbowAmount;
            float _WaveHeight;
        CBUFFER_END

        float WaterHeight(float2 m, float t)
        {
            float2 p = float2(m.x * 1.7, (m.y - t * _FlowSpeed) * 0.55);
            return BWK_ValueNoise(p) * 0.6 + BWK_ValueNoise(p * 2.3 + 7.1) * 0.4;
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

            half4 frag(Varyings i) : SV_Target
            {
                UNITY_SETUP_INSTANCE_ID(i);
                float t = _Time.y;
                float2 m = i.meters;
                // Ripple normal from finite differences of the flowing height field.
                float e = 0.06;
                float h0 = WaterHeight(m, t);
                float hx = WaterHeight(m + float2(e, 0), t);
                float hy = WaterHeight(m + float2(0, e), t);
                half3 bitangent = cross(i.normalWS, i.tangentWS.xyz) * i.tangentWS.w;
                half3 n = normalize(i.normalWS - (i.tangentWS.xyz * (hx - h0) + bitangent * (hy - h0)) / e * _RippleStrength * 0.08);

                // Long streaks stretched along the flow direction.
                float flowY = m.y - t * _FlowSpeed;
                // long thin speed streaks (reference: bright light lines racing down the slide)
                float s1 = BWK_Fbm(float2(m.x * 3.4 * _StreakDensity, flowY * 0.11 * _StreakDensity));
                float s2 = BWK_ValueNoise(float2(m.x * 7.0 * _StreakDensity, flowY * 0.35 * _StreakDensity + 3.0));
                half streak = smoothstep(0.58, 0.8, s1 * 0.72 + s2 * 0.28) * _StreakAmount;

                float across = abs(i.uv.x - 0.5) * 2.0; // 0 centre, 1 at the walls
                half3 baseCol = lerp(_ShallowColor.rgb, _DeepColor.rgb, saturate(0.35 + h0 * 0.5 - across * 0.25));
                baseCol = lerp(baseCol, _EdgeTint.rgb, smoothstep(0.55, 1.0, across) * _EdgeTintAmount);
                half foam = smoothstep(0.82, 0.97, across + (s2 - 0.5) * 0.12) * _EdgeFoam;
                // rainbow sheen picked up from the candy rails (cyan / yellow / pink bands toward the banks)
                half3 rainbow = BWK_Rainbow(across * 0.9 + s1 * 0.6 - flowY * 0.015);
                baseCol = lerp(baseCol, rainbow, smoothstep(0.45, 0.95, across) * _RainbowAmount);
                half3 albedo = lerp(baseCol, _StreakColor.rgb, saturate(streak + foam));
                half smooth = lerp(_Smoothness, 0.45, saturate(streak + foam));

                half3 viewDir = GetWorldSpaceNormalizeViewDir(i.positionWS);
                half3 emission = albedo * _Glow;
                // sparkle glints riding the flow: sparse tiny HDR points, bloom turns them into twinkles
                float2 sp = float2(m.x * 8.0, flowY * 2.6);
                float2 spc = floor(sp);
                float2 spl = frac(sp) - 0.5 - (float2(BWK_Hash21(spc + 3.3), BWK_Hash21(spc + 7.7)) - 0.5) * 0.6;
                half spark = step(0.94, BWK_Hash21(spc)) * smoothstep(0.13, 0.0, length(spl * float2(1.0, 0.6)));
                emission += _StreakColor.rgb * spark * 2.6 * _SparkleAmount * (1.0 - foam);
                half4 c = BWK_PBR(i.positionWS, i.positionCS, n, viewDir, albedo, 0.0, smooth, 1.0, emission, 1.0, i.fog);
                return c;
            }
            ENDHLSL
        }
    }
    FallBack Off
}

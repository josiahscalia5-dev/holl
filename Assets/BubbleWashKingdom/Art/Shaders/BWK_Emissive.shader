// Unlit HDR emissive surface with a hot white core, gentle pulse and an optional marquee chase pattern.
// Used for neon star tubes (_Chase = 0) and the warm ring bulbs (_Chase = 1). Bloom turns the HDR values into glow.
Shader "BWK/Emissive"
{
    Properties
    {
        [HDR] _Color ("Color", Color) = (0.2, 1.0, 1.0, 1)
        _Intensity ("Intensity", Float) = 3
        _CoreWhite ("Hot Core Whiteness", Range(0,1)) = 0.45
        _PulseSpeed ("Pulse Speed", Float) = 1.2
        _PulseAmount ("Pulse Amount", Range(0,1)) = 0.15
        _Chase ("Marquee Chase", Range(0,1)) = 0
        _ChaseScale ("Chase Scale (1/m)", Float) = 1.6
        _ChaseSpeed ("Chase Speed", Float) = 1.5
        _ChaseMin ("Chase Minimum", Range(0,1)) = 0.45
        _FogAmount ("Fog Amount", Range(0,1)) = 0.35
        _HaloBoost ("Grazing Halo Boost", Range(0,2)) = 0.6
        _CorePower ("Hot Core Sharpness", Range(1,16)) = 4
        _EdgeSaturate ("Edge Saturation Boost", Range(0,1)) = 0
    }
    SubShader
    {
        Tags { "RenderType"="Opaque" "RenderPipeline"="UniversalPipeline" "Queue"="Geometry" }
        HLSLINCLUDE
        #include "BWKCommon.hlsl"
        CBUFFER_START(UnityPerMaterial)
            half4 _Color;
            half _Intensity, _CoreWhite, _PulseSpeed, _PulseAmount, _Chase, _ChaseScale, _ChaseSpeed, _ChaseMin, _FogAmount, _HaloBoost;
            half _CorePower, _EdgeSaturate;
        CBUFFER_END
        ENDHLSL
        Pass
        {
            Name "Unlit"
            Tags { "LightMode"="UniversalForward" }
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_fog
            #pragma multi_compile_instancing
            struct Attributes { float4 positionOS : POSITION; float3 normalOS : NORMAL; UNITY_VERTEX_INPUT_INSTANCE_ID };
            struct Varyings { float4 positionCS : SV_POSITION; float3 positionWS : TEXCOORD0; half3 normalWS : TEXCOORD1; half fog : TEXCOORD2; float3 pivotWS : TEXCOORD3; UNITY_VERTEX_INPUT_INSTANCE_ID };
            Varyings vert(Attributes i)
            {
                Varyings o = (Varyings)0;
                UNITY_SETUP_INSTANCE_ID(i);
                UNITY_TRANSFER_INSTANCE_ID(i, o);
                VertexPositionInputs p = GetVertexPositionInputs(i.positionOS.xyz);
                o.positionCS = p.positionCS;
                o.positionWS = p.positionWS;
                o.normalWS = TransformObjectToWorldNormal(i.normalOS);
                o.fog = ComputeFogFactor(p.positionCS.z);
                o.pivotWS = p.positionWS;
                return o;
            }
            half4 frag(Varyings i) : SV_Target
            {
                half3 v = GetWorldSpaceNormalizeViewDir(i.positionWS);
                half facing = saturate(dot(normalize(i.normalWS), v));
                // saturated colour at grazing angles (reads as a coloured halo through bloom), hot core facing the camera
                // _EdgeSaturate pushes the rim toward the pure hue (squares the colour, renormalised) so neon tubes and bulbs keep a
                // deep saturated edge around the white-hot core after tonemapping (0 = previous look).
                half3 hue = _Color.rgb * _Color.rgb / max(max(_Color.r, max(_Color.g, _Color.b)), 1e-3);
                half3 edge = lerp(_Color.rgb, hue, _EdgeSaturate);
                half3 col = lerp(edge * (1.0 + _HaloBoost * (1.0 - facing)), half3(1, 1, 1), pow(facing, _CorePower) * _CoreWhite);
                float seed = dot(floor(i.pivotWS * 2.0), float3(0.31, 0.17, 0.53));
                half pulse = 1.0 + sin(_Time.y * _PulseSpeed * 6.2831 + seed * 6.2831) * _PulseAmount;
                float chasePhase = frac(dot(i.positionWS, float3(0.57, 0.31, 0.77)) * _ChaseScale - _Time.y * _ChaseSpeed);
                half chase = lerp(1.0, lerp(_ChaseMin, 1.0, smoothstep(0.35, 0.0, abs(chasePhase - 0.5) - 0.15)), _Chase);
                half3 c = col * _Intensity * pulse * chase;
                c = lerp(c, MixFog(c, i.fog), _FogAmount);
                return half4(c, 1);
            }
            ENDHLSL
        }
    }
    FallBack Off
}

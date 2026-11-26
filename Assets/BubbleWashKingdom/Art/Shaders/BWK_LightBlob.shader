// Soft contact shadow / light pool card (Agent 4 - lighting). A flat quad that multiplies the surface below by a tinted,
// radially soft falloff: dark violet contact shadow under the mascot (_Mode 0) or, with _Mode 1, an additive soft glow
// pool (warm light spill on the water / wall). Mobile friendly: one transparent pass, no textures.
Shader "BWK/LightBlob"
{
    Properties
    {
        _Color ("Shadow / Glow Colour", Color) = (0.32, 0.16, 0.55, 1)
        _Strength ("Strength", Range(0, 2)) = 0.6
        _Softness ("Edge Softness", Range(0.01, 1)) = 0.75
        _Core ("Core Tightness", Range(0.5, 4)) = 1.4
        [Enum(Multiply,0,Additive,1)] _Mode ("Mode", Float) = 0
        _NearFade ("Fade out closer than (m, 0 = off)", Float) = 0
        [HideInInspector] _SrcBlend ("Src", Float) = 2
        [HideInInspector] _DstBlend ("Dst", Float) = 0
    }
    SubShader
    {
        Tags { "RenderType"="Transparent" "RenderPipeline"="UniversalPipeline" "Queue"="Transparent-20" "IgnoreProjector"="True" }
        Pass
        {
            Name "Blob"
            Tags { "LightMode"="UniversalForward" }
            Blend [_SrcBlend] [_DstBlend]
            ZWrite Off
            ZTest LEqual
            Cull Off
            Offset -2, -2
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_fog
            #pragma multi_compile_instancing
            #include "BWKCommon.hlsl"
            CBUFFER_START(UnityPerMaterial)
                half4 _Color;
                half _Strength, _Softness, _Core, _Mode, _SrcBlend, _DstBlend, _NearFade;
            CBUFFER_END
            struct Attributes { float4 positionOS : POSITION; float2 uv : TEXCOORD0; half4 color : COLOR; UNITY_VERTEX_INPUT_INSTANCE_ID };
            struct Varyings { float4 positionCS : SV_POSITION; float2 uv : TEXCOORD0; half fog : TEXCOORD1; half4 color : TEXCOORD2; half near : TEXCOORD3; UNITY_VERTEX_INPUT_INSTANCE_ID };
            Varyings vert(Attributes i)
            {
                Varyings o = (Varyings)0;
                UNITY_SETUP_INSTANCE_ID(i);
                UNITY_TRANSFER_INSTANCE_ID(i, o);
                VertexPositionInputs p = GetVertexPositionInputs(i.positionOS.xyz);
                o.positionCS = p.positionCS;
                o.uv = i.uv;
                o.fog = ComputeFogFactor(p.positionCS.z);
                o.color = i.color;
                // far light glows (vanishing point): fade out as the camera approaches, so passing through never flashes
                o.near = _NearFade > 0.0 ? saturate((distance(p.positionWS, GetCameraPositionWS()) - _NearFade) / _NearFade) : 1.0;
                return o;
            }
            half4 frag(Varyings i) : SV_Target
            {
                UNITY_SETUP_INSTANCE_ID(i);
                half r = length(i.uv * 2.0 - 1.0);
                half a = saturate(1.0 - smoothstep(1.0 - _Softness, 1.0, r));
                a = pow(a, _Core) * _Strength * i.near;
                half keep = 1.0h; // fades out with distance fog (1 = no fog)
            #if defined(FOG_LINEAR) || defined(FOG_EXP) || defined(FOG_EXP2)
                keep = saturate(ComputeFogIntensity(i.fog));
            #endif
                if (_Mode < 0.5)
                {
                    // multiply: 1 = untouched, towards _Color where the blob is dense
                    half3 m = lerp(half3(1, 1, 1), _Color.rgb, saturate(a * keep));
                    return half4(m, 1);
                }
                half3 c = _Color.rgb * a * keep;
                return half4(c, 1);
            }
            ENDHLSL
        }
    }
    FallBack Off
}

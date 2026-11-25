// Unlit animated glow surfaces:
//  _Mode 0 = pipe liquid: bright bands flowing along UV.y
//  _Mode 1 = chamber swirl: rainbow water spiralling around the UV centre with foam streaks (portholes)
//  _Mode 2 = boost chevron: cyan glow with a bright pulse travelling forward along UV.y and a white rim
//  _Mode 3 = portal rays: additive radial light rays (use with the Additive blend variant below)
Shader "BWK/FlowGlow"
{
    Properties
    {
        [HDR] _ColorA ("Color A", Color) = (0.3, 0.9, 1.0, 1)
        [HDR] _ColorB ("Color B", Color) = (1.0, 0.45, 0.9, 1)
        _Intensity ("Intensity", Float) = 2
        _Speed ("Speed", Float) = 1
        _Scale ("Scale", Float) = 3
        _Mode ("Mode (0 pipe, 1 swirl, 2 chevron, 3 rays)", Float) = 0
        _RayCount ("Ray Count", Float) = 14
        [Enum(UnityEngine.Rendering.BlendMode)] _SrcBlend ("Src Blend", Float) = 1
        [Enum(UnityEngine.Rendering.BlendMode)] _DstBlend ("Dst Blend", Float) = 0
        [Enum(Off,0,On,1)] _ZWrite ("ZWrite", Float) = 1
    }
    SubShader
    {
        Tags { "RenderType"="Opaque" "RenderPipeline"="UniversalPipeline" "Queue"="Geometry" }
        HLSLINCLUDE
        #include "BWKCommon.hlsl"
        CBUFFER_START(UnityPerMaterial)
            half4 _ColorA, _ColorB;
            half _Intensity, _Speed, _Scale, _Mode, _RayCount;
            half _SrcBlend, _DstBlend, _ZWrite;
        CBUFFER_END
        ENDHLSL
        Pass
        {
            Name "Unlit"
            Tags { "LightMode"="UniversalForward" }
            Blend [_SrcBlend] [_DstBlend]
            ZWrite [_ZWrite]
            Cull Off
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_fog
            #pragma multi_compile_instancing
            struct Attributes { float4 positionOS : POSITION; float2 uv : TEXCOORD0; half4 color : COLOR; UNITY_VERTEX_INPUT_INSTANCE_ID };
            struct Varyings { float4 positionCS : SV_POSITION; float2 uv : TEXCOORD0; half fog : TEXCOORD1; half4 color : TEXCOORD2; UNITY_VERTEX_INPUT_INSTANCE_ID };
            Varyings vert(Attributes i)
            {
                Varyings o = (Varyings)0;
                UNITY_SETUP_INSTANCE_ID(i);
                UNITY_TRANSFER_INSTANCE_ID(i, o);
                o.positionCS = TransformObjectToHClip(i.positionOS.xyz);
                o.uv = i.uv;
                o.fog = ComputeFogFactor(o.positionCS.z);
                o.color = i.color;
                return o;
            }
            half4 frag(Varyings i) : SV_Target
            {
                float t = _Time.y * _Speed;
                half3 c;
                half a = 1.0;
                if (_Mode < 0.5)
                {
                    float band = BWK_Fbm(float2(i.uv.x * 2.0, i.uv.y * _Scale - t));
                    c = lerp(_ColorA.rgb, _ColorB.rgb, smoothstep(0.35, 0.75, band)) * (0.75 + band * 0.6);
                }
                else if (_Mode < 1.5)
                {
                    float2 p = i.uv - 0.5;
                    float r = length(p) * 2.0;
                    float ang = atan2(p.y, p.x) / 6.28318;
                    float swirl = ang + r * 0.9 - t * 0.12;
                    half3 rainbow = BWK_Rainbow(swirl * 1.0 + 0.05 * BWK_ValueNoise(p * 8.0 + t));
                    float foam = smoothstep(0.62, 0.9, BWK_Fbm(float2(swirl * 9.0, r * 4.0 - t * 0.6)));
                    c = lerp(rainbow * lerp(_ColorA.rgb, half3(1, 1, 1), 0.25), half3(1, 1, 1), foam * 0.8);
                    c *= lerp(1.15, 0.55, saturate(r)); // darker toward the drum rim
                }
                else if (_Mode < 2.5)
                {
                    float pulse = frac(i.uv.y * 0.5 - t);
                    float glow = smoothstep(0.0, 0.25, pulse) * smoothstep(0.6, 0.25, pulse);
                    float rim = smoothstep(0.75, 0.95, abs(i.uv.x - 0.5) * 2.0);
                    c = lerp(_ColorA.rgb * (0.7 + glow * 1.3), half3(1, 1, 1), rim * 0.8);
                }
                else
                {
                    float2 p = i.uv - 0.5;
                    float r = length(p) * 2.0;
                    float ang = atan2(p.y, p.x);
                    float rays = pow(abs(sin(ang * _RayCount * 0.5 + t * 0.4)), 6.0) * 0.8 + 0.25;
                    float fall = saturate(1.0 - r);
                    c = lerp(_ColorB.rgb, _ColorA.rgb, fall) * rays * fall * fall;
                    a = saturate(rays * fall);
                }
                c *= _Intensity * i.color.rgb;
                c = MixFog(c, i.fog);
                return half4(c, a);
            }
            ENDHLSL
        }
    }
    FallBack Off
}

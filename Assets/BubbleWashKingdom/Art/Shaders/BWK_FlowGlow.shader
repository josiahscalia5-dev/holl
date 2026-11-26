// Unlit animated glow surfaces:
//  _Mode 0 = pipe liquid: bright bands flowing along UV.y
//  _Mode 1 = chamber window (reference key 7.5 s / 10.5 s): a bold cartoon rainbow arch over light-blue water, puffy
//            white foam clouds banked at the bottom and drifting, faint swirl streaks; the picture churns gently.
//            "Up" = -U (SM_ChamberWindow / SM_Porthole swirl disc as placed by SceneBuilder.BuildPortholes).
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
            static const half3 BWK_RB[6] = { half3(1.0, 0.27, 0.40), half3(1.0, 0.58, 0.20), half3(1.0, 0.86, 0.30),
                                             half3(0.40, 0.86, 0.50), half3(0.28, 0.68, 1.0), half3(0.58, 0.40, 1.0) };
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
                    float2 q = float2(p.y, -p.x) * 2.0;                       // q.y = world up on the windows
                    float rd = length(q);
                    float ch = sin(t * 0.35) * 0.10;                            // gentle churn
                    float cs = cos(ch), sn = sin(ch);
                    q = float2(cs * q.x - sn * q.y, sn * q.x + cs * q.y);
                    float2 c0 = q - float2(0.0, -0.62);                         // arch centre below the middle
                    float aAng = atan2(c0.y, c0.x);
                    float ar = length(c0) + 0.03 * sin(aAng * 5.0 + t * 1.3) + 0.05 * (BWK_ValueNoise(q * 4.0 + t * 0.35) - 0.5);
                    float bt = (ar - 0.52) / 0.78;                              // 0 inner (violet) .. 1 outer (red)
                    float sb = saturate(bt) * 6.0;
                    float k = min(floor(sb), 5.0);
                    float fb = sb - k;
                    half3 ca = BWK_RB[5 - (int)k];
                    half3 cb = BWK_RB[5 - (int)min(k + 1.0, 5.0)];
                    float aw = fwidth(sb) * 1.5 + 0.03;
                    half3 rain = lerp(ca, cb, smoothstep(1.0 - aw, 1.0, fb));
                    float edgeW = fwidth(bt) * 1.5 + 0.01;
                    float arch = smoothstep(-edgeW, edgeW, bt) * (1.0 - smoothstep(1.0 - edgeW, 1.0 + edgeW, bt));
                    half3 sky = lerp(half3(0.55, 0.85, 1.0), lerp(_ColorA.rgb, half3(0.92, 0.97, 1.0), 0.5), saturate(q.y * 0.5 + 0.5));
                    half3 col = lerp(sky, rain * 1.05, arch);
                    // puffy foam: a dense bank at the bottom + drifting puffs
                    float cl = BWK_Fbm(q * 2.3 + float2(t * 0.08, 0.0));
                    float bank = smoothstep(0.0, 0.18, cl * 0.95 - (q.y + 0.38) * 0.85);
                    float puffs = smoothstep(0.64, 0.72, BWK_Fbm(q * 2.8 + float2(-t * 0.12, 3.1)));
                    float cloud = saturate(bank + puffs * 0.9);
                    half3 cloudCol = lerp(half3(0.80, 0.84, 1.0), half3(1.0, 1.0, 1.0), saturate(cl * 1.5 - 0.1));
                    col = lerp(col, cloudCol, cloud);
                    // faint swirl streaks (the water turning in the drum)
                    float swirl = atan2(q.y, q.x) / 6.28318 + rd * 0.9 - t * 0.12;
                    float foam = smoothstep(0.7, 0.92, BWK_Fbm(float2(swirl * 9.0, rd * 4.0 - t * 0.6)));
                    col = lerp(col, half3(1, 1, 1), foam * 0.3 * (1.0 - cloud));
                    c = col * lerp(1.08, 0.62, smoothstep(0.78, 1.0, rd));     // darker toward the drum rim
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

// Lead 8d2d815d 2026-11-27 (owner 19:5x, approved "drum wall only"): ONE protected camera-projection test of the S2 door drum
// (MouthDrum_r7 chunks, track 40.2 -> 62 m). Used only by ProjectionS2Test.cs in no-save previews; never by the built game.
// _Mode 0 = visibility pass (float RT via CommandBuffer): RG = (around 0..1, along 0..1 over _D0.._D1), B = 1 (drum texel visible)
// _Mode 1 = black occluder (depth only, everything that is not the drum)
// _Mode 2 = display: the projected texture on the real drum surface (unlit; _Gain / _Lift = tone calibration against the post chain)
// Drum chunk UVs (SplineMeshDeformer distanceUVTile 4): uv.x = around fraction, uv.y = track distance / 4 (BWK_DrumWall m.y = uv.y * 4).
Shader "Hidden/BWK/ProjTest"
{
    Properties
    {
        _Mode ("Mode", Float) = 2
        _ProjTex ("Projected texture (around x along)", 2D) = "gray" {}
        _D0 ("Along start (m)", Float) = 40.2
        _D1 ("Along end (m)", Float) = 62
        _Gain ("Gain", Float) = 1
    }
    SubShader
    {
        Tags { "RenderType"="Opaque" "RenderPipeline"="UniversalPipeline" "Queue"="Geometry" }
        Pass
        {
            Cull Off ZWrite On ZTest LEqual
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            TEXTURE2D(_ProjTex); SAMPLER(sampler_ProjTex);
            CBUFFER_START(UnityPerMaterial)
                float4 _ProjTex_ST;
                float _Mode, _D0, _D1, _Gain;
            CBUFFER_END
            struct A { float4 positionOS : POSITION; float2 uv : TEXCOORD0; };
            struct V { float4 positionCS : SV_POSITION; float2 uv : TEXCOORD0; };
            V vert(A v) { V o; o.positionCS = TransformObjectToHClip(v.positionOS.xyz); o.uv = v.uv; return o; }
            float4 frag(V i) : SV_Target
            {
                float t = (i.uv.y * 4.0 - _D0) / (_D1 - _D0);
                if (_Mode < 0.5) return float4(frac(i.uv.x), t, 1.0, 1.0);
                if (_Mode < 1.5) return float4(0, 0, 0, 1);
                float3 c = SAMPLE_TEXTURE2D(_ProjTex, sampler_ProjTex, float2(i.uv.x, saturate(t))).rgb;
                return float4(c * _Gain, 1.0);
            }
            ENDHLSL
        }
    }
}

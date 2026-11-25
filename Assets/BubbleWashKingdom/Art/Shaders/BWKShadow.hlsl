#ifndef BWK_SHADOW_INCLUDED
#define BWK_SHADOW_INCLUDED
// Minimal shadow-caster pass shared by the custom opaque shaders.
// Include after the shader's HLSLINCLUDE block (which defines UnityPerMaterial and pulls in BWKCommon.hlsl).
#include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Shadows.hlsl"

float3 _LightDirection;
float3 _LightPosition;

struct ShadowAttributes
{
    float4 positionOS : POSITION;
    float3 normalOS : NORMAL;
    float2 uv : TEXCOORD0;
    float2 uv1 : TEXCOORD1;
    UNITY_VERTEX_INPUT_INSTANCE_ID
};

struct ShadowVaryings
{
    float4 positionCS : SV_POSITION;
    float2 uv1 : TEXCOORD0;
};

ShadowVaryings ShadowVert(ShadowAttributes i)
{
    ShadowVaryings o;
    UNITY_SETUP_INSTANCE_ID(i);
    float3 positionWS = TransformObjectToWorld(i.positionOS.xyz);
    float3 normalWS = TransformObjectToWorldNormal(i.normalOS);
#if _CASTING_PUNCTUAL_LIGHT_SHADOW
    float3 lightDir = normalize(_LightPosition - positionWS);
#else
    float3 lightDir = _LightDirection;
#endif
    float4 positionCS = TransformWorldToHClip(ApplyShadowBias(positionWS, normalWS, lightDir));
#if UNITY_REVERSED_Z
    positionCS.z = min(positionCS.z, UNITY_NEAR_CLIP_VALUE);
#else
    positionCS.z = max(positionCS.z, UNITY_NEAR_CLIP_VALUE);
#endif
    o.positionCS = positionCS;
    o.uv1 = i.uv1;
    return o;
}

half4 ShadowFrag(ShadowVaryings i) : SV_Target
{
#ifdef BWK_SHADOW_SKIP_SHELLS
    clip(0.15 - i.uv1.x); // fur: only the skin layer casts shadows
#endif
    return 0;
}
#endif

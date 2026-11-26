#ifndef BWK_COMMON_INCLUDED
#define BWK_COMMON_INCLUDED

#include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
#include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"

// ------------------------------------------------------------------ noise
float BWK_Hash21(float2 p)
{
    p = frac(p * float2(123.34, 456.21));
    p += dot(p, p + 45.32);
    return frac(p.x * p.y);
}

float BWK_Hash31(float3 p)
{
    p = frac(p * 0.3183099 + 0.1);
    p *= 17.0;
    return frac(p.x * p.y * p.z * (p.x + p.y + p.z));
}

float BWK_ValueNoise(float2 p)
{
    float2 i = floor(p);
    float2 f = frac(p);
    float2 u = f * f * (3.0 - 2.0 * f);
    float a = BWK_Hash21(i);
    float b = BWK_Hash21(i + float2(1, 0));
    float c = BWK_Hash21(i + float2(0, 1));
    float d = BWK_Hash21(i + float2(1, 1));
    return lerp(lerp(a, b, u.x), lerp(c, d, u.x), u.y);
}

float BWK_ValueNoise3(float3 p)
{
    float3 i = floor(p);
    float3 f = frac(p);
    float3 u = f * f * (3.0 - 2.0 * f);
    float n000 = BWK_Hash31(i);
    float n100 = BWK_Hash31(i + float3(1, 0, 0));
    float n010 = BWK_Hash31(i + float3(0, 1, 0));
    float n110 = BWK_Hash31(i + float3(1, 1, 0));
    float n001 = BWK_Hash31(i + float3(0, 0, 1));
    float n101 = BWK_Hash31(i + float3(1, 0, 1));
    float n011 = BWK_Hash31(i + float3(0, 1, 1));
    float n111 = BWK_Hash31(i + float3(1, 1, 1));
    return lerp(lerp(lerp(n000, n100, u.x), lerp(n010, n110, u.x), u.y),
                lerp(lerp(n001, n101, u.x), lerp(n011, n111, u.x), u.y), u.z);
}

float BWK_Fbm(float2 p)
{
    float v = 0.0;
    float a = 0.5;
    for (int i = 0; i < 4; i++)
    {
        v += a * BWK_ValueNoise(p);
        p = p * 2.03 + float2(17.1, 9.7);
        a *= 0.5;
    }
    return v;
}

half3 BWK_Rainbow(float t)
{
    // smooth saturated rainbow palette (IQ cosine palette)
    return saturate(0.5 + 0.5 * cos(6.28318 * (t + float3(0.0, 0.33, 0.67))));
}

half BWK_Fresnel(half3 n, half3 v, half power)
{
    return pow(1.0 - saturate(dot(n, v)), power);
}

// ------------------------------------------------------------------ lighting
// Wraps URP's UniversalFragmentPBR so custom shaders get the main light with shadows, additional lights,
// SH ambient, reflection probes and fog exactly like URP/Lit.
// r8 (lighting): BWK_PBR_Lit = the same lit result WITHOUT fog, so a material can grade its own lit colour (BWK_DrumWall:
// desaturate the violet light response toward grey-lavender metal) before the fog is mixed in.
half4 BWK_PBR_Lit(float3 positionWS, float4 positionCS, half3 normalWS, half3 viewDirWS,
                  half3 albedo, half metallic, half smoothness, half occlusion, half3 emission, half alpha, half fogFactor)
{
    InputData inputData = (InputData)0;
    inputData.positionWS = positionWS;
    inputData.positionCS = positionCS;
    inputData.normalWS = normalWS;
    inputData.viewDirectionWS = viewDirWS;
#if defined(_MAIN_LIGHT_SHADOWS) || defined(_MAIN_LIGHT_SHADOWS_CASCADE)
    inputData.shadowCoord = TransformWorldToShadowCoord(positionWS);
#else
    inputData.shadowCoord = float4(0, 0, 0, 0);
#endif
    inputData.fogCoord = fogFactor;
    inputData.vertexLighting = half3(0, 0, 0);
    inputData.bakedGI = SampleSH(normalWS);
    inputData.normalizedScreenSpaceUV = GetNormalizedScreenSpaceUV(positionCS);
    inputData.shadowMask = half4(1, 1, 1, 1);

    SurfaceData s = (SurfaceData)0;
    s.albedo = albedo;
    s.metallic = metallic;
    s.specular = half3(0, 0, 0);
    s.smoothness = smoothness;
    s.normalTS = half3(0, 0, 1);
    s.emission = emission;
    s.occlusion = occlusion;
    s.alpha = alpha;
    return UniversalFragmentPBR(inputData, s);
}
half4 BWK_PBR(float3 positionWS, float4 positionCS, half3 normalWS, half3 viewDirWS,
              half3 albedo, half metallic, half smoothness, half occlusion, half3 emission, half alpha, half fogFactor)
{
    half4 c = BWK_PBR_Lit(positionWS, positionCS, normalWS, viewDirWS, albedo, metallic, smoothness, occlusion, emission, alpha, fogFactor);
    c.rgb = MixFog(c.rgb, fogFactor);
    return c;
}

// Soft stylised diffuse used by fur and foam: wrap lighting + SH + main-light shadows.
half3 BWK_WrapLight(float3 positionWS, half3 normalWS, half wrap)
{
#if defined(_MAIN_LIGHT_SHADOWS) || defined(_MAIN_LIGHT_SHADOWS_CASCADE)
    float4 shadowCoord = TransformWorldToShadowCoord(positionWS);
#else
    float4 shadowCoord = float4(0, 0, 0, 0);
#endif
    Light mainLight = GetMainLight(shadowCoord);
    half ndl = saturate((dot(normalWS, mainLight.direction) + wrap) / (1.0 + wrap));
    half shadow = lerp(0.55, 1.0, mainLight.shadowAttenuation);
    half3 c = mainLight.color * ndl * shadow + SampleSH(normalWS);
#if defined(_ADDITIONAL_LIGHTS)
    uint count = GetAdditionalLightsCount();
    for (uint li = 0u; li < count; ++li)
    {
        Light l = GetAdditionalLight(li, positionWS);
        half nd = saturate((dot(normalWS, l.direction) + wrap) / (1.0 + wrap));
        c += l.color * nd * l.distanceAttenuation;
    }
#endif
    return c;
}

#endif

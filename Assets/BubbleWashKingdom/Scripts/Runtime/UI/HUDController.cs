using UnityEngine;
using UnityEngine.UI;

namespace BubbleWash
{
    /// <summary>
    /// Minimal playful HUD built in code (no prefab dependencies): coin and gem counters, swipe hint and the
    /// section-complete banner. Uses the built-in runtime font so it works in every build.
    /// </summary>
    public class HUDController : MonoBehaviour
    {
        public TrackItemRegistry items;
        public RunnerController runner;

        Text coinText, gemText, hintText, completeText;
        GameObject hintGo, completeGo, fadeGo;
        int shownCoins = -1, shownGems = -1;
        float coinPulse, gemPulse;
        RectTransform coinIcon, gemIcon;
        // finishing sequence polish (2026-11-26): the banner pops in, a soft violet fade bridges the loop restart
        CanvasGroup completeGroup;
        Image fadeImage;
        float completeAnim = 1f, fadeAlpha, fadeTarget, fadeSpeed = 2f;
        static readonly Color FadeColor = new Color(0.16f, 0.07f, 0.30f, 1f);

        static readonly Color Gold = new Color(1f, 0.82f, 0.25f);
        static readonly Color Purple = new Color(0.72f, 0.35f, 1f);

        void Awake() { Build(); }

        void Build()
        {
            var canvasGo = new GameObject("HUD Canvas", typeof(Canvas), typeof(CanvasScaler), typeof(GraphicRaycaster));
            canvasGo.transform.SetParent(transform, false);
            var canvas = canvasGo.GetComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            canvas.sortingOrder = 10;
            var scaler = canvasGo.GetComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1080, 1920);
            scaler.matchWidthOrHeight = 0.5f;
            Font font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");

            coinIcon = Pill(canvasGo.transform, "Coins", new Vector2(0f, 1f), new Vector2(40f, -40f), Gold, font, out coinText);
            gemIcon = Pill(canvasGo.transform, "Gems", new Vector2(1f, 1f), new Vector2(-40f, -40f), Purple, font, out gemText);
            gemIcon.localRotation = Quaternion.Euler(0f, 0f, 45f);

            hintGo = new GameObject("Hint", typeof(RectTransform));
            hintGo.transform.SetParent(canvasGo.transform, false);
            var hr = (RectTransform)hintGo.transform;
            // OWNER 2026-11-27 06:58 (s19 + his S2 sheet 08): the hint covered the seated mascot's feet / splash at 18 % height
            // in portrait gameplay -> smaller, at the very bottom edge (below his feet, over the near water only)
            hr.anchorMin = hr.anchorMax = new Vector2(0.5f, 0.055f);
            hr.sizeDelta = new Vector2(1000f, 120f);
            hintText = MakeText(hintGo.transform, font, 40, TextAnchor.MiddleCenter, "Swipe  ◀ ▶  to steer\nSwipe  ▲  to jump");

            completeGo = new GameObject("Complete", typeof(RectTransform));
            completeGo.transform.SetParent(canvasGo.transform, false);
            var cr = (RectTransform)completeGo.transform;
            // 2026-11-26 finishing sequence: the banner sits above the golden portal burst on a soft violet panel so it
            // stays readable over the bright portal (it was unreadable white-on-white in the round-7 recording)
            cr.anchorMin = cr.anchorMax = new Vector2(0.5f, 0.79f);
            cr.sizeDelta = new Vector2(860f, 270f);
            var panel = new GameObject("Panel", typeof(RectTransform), typeof(Image));
            panel.transform.SetParent(completeGo.transform, false);
            var prt = (RectTransform)panel.transform;
            prt.anchorMin = Vector2.zero; prt.anchorMax = Vector2.one;
            prt.offsetMin = prt.offsetMax = Vector2.zero;
            var pimg = panel.GetComponent<Image>();
            pimg.sprite = RoundedSprite();
            pimg.type = Image.Type.Sliced;
            pimg.color = new Color(0.20f, 0.06f, 0.36f, 0.66f);
            pimg.raycastTarget = false;
            completeText = MakeText(completeGo.transform, font, 76, TextAnchor.MiddleCenter, "");
            completeGroup = completeGo.AddComponent<CanvasGroup>();
            completeGroup.blocksRaycasts = false;
            completeGo.SetActive(false);

            fadeGo = new GameObject("Fade", typeof(RectTransform), typeof(Image));
            fadeGo.transform.SetParent(canvasGo.transform, false);
            var fr = (RectTransform)fadeGo.transform;
            fr.anchorMin = Vector2.zero; fr.anchorMax = Vector2.one;
            fr.offsetMin = fr.offsetMax = Vector2.zero;
            fadeImage = fadeGo.GetComponent<Image>();
            fadeImage.raycastTarget = false;
            fadeImage.color = new Color(FadeColor.r, FadeColor.g, FadeColor.b, 0f);
            fadeGo.transform.SetAsLastSibling();
            fadeGo.SetActive(false);
        }

        /// <summary>Fades a full-screen soft violet overlay to <paramref name="alpha"/> over <paramref name="seconds"/>.</summary>
        public void Fade(float alpha, float seconds)
        {
            fadeTarget = Mathf.Clamp01(alpha);
            fadeSpeed = 1f / Mathf.Max(0.01f, seconds);
        }

        RectTransform Pill(Transform parent, string name, Vector2 anchor, Vector2 offset, Color iconColor, Font font, out Text label)
        {
            var go = new GameObject(name, typeof(RectTransform), typeof(Image));
            go.transform.SetParent(parent, false);
            var rt = (RectTransform)go.transform;
            rt.anchorMin = rt.anchorMax = rt.pivot = anchor;
            rt.anchoredPosition = offset;
            rt.sizeDelta = new Vector2(300f, 110f);
            var bg = go.GetComponent<Image>();
            bg.sprite = RoundedSprite();
            bg.type = Image.Type.Sliced;
            bg.color = new Color(0.22f, 0.08f, 0.38f, 0.55f);

            var icon = new GameObject("Icon", typeof(RectTransform), typeof(Image));
            icon.transform.SetParent(go.transform, false);
            var irt = (RectTransform)icon.transform;
            irt.anchorMin = irt.anchorMax = new Vector2(anchor.x < 0.5f ? 0f : 1f, 0.5f);
            irt.anchoredPosition = new Vector2(anchor.x < 0.5f ? 60f : -60f, 0f);
            irt.sizeDelta = new Vector2(70f, 70f);
            icon.GetComponent<Image>().color = iconColor;

            label = MakeText(go.transform, font, 64, anchor.x < 0.5f ? TextAnchor.MiddleRight : TextAnchor.MiddleLeft, "0");
            var lr = label.rectTransform;
            lr.anchorMin = new Vector2(0f, 0f); lr.anchorMax = new Vector2(1f, 1f);
            lr.offsetMin = new Vector2(anchor.x < 0.5f ? 110f : 24f, 0f);
            lr.offsetMax = new Vector2(anchor.x < 0.5f ? -24f : -110f, 0f);
            return irt;
        }

        static Sprite roundedSprite;

        /// <summary>Procedural 9-sliced rounded-rectangle sprite (no texture asset needed) for the HUD pills and banner.</summary>
        static Sprite RoundedSprite()
        {
            if (roundedSprite != null) return roundedSprite;
            const int S = 64; const float R = 26f;
            var tex = new Texture2D(S, S, TextureFormat.RGBA32, false) { wrapMode = TextureWrapMode.Clamp, filterMode = FilterMode.Bilinear };
            var px = new Color32[S * S];
            for (int y = 0; y < S; y++)
                for (int x = 0; x < S; x++)
                {
                    float dx = Mathf.Max(0f, Mathf.Max(R - x - 0.5f, x + 0.5f - (S - R)));
                    float dy = Mathf.Max(0f, Mathf.Max(R - y - 0.5f, y + 0.5f - (S - R)));
                    float d = Mathf.Sqrt(dx * dx + dy * dy);
                    px[y * S + x] = new Color32(255, 255, 255, (byte)(255f * Mathf.Clamp01(R - d + 0.5f)));
                }
            tex.SetPixels32(px);
            tex.Apply(false, true);
            roundedSprite = Sprite.Create(tex, new Rect(0, 0, S, S), new Vector2(0.5f, 0.5f), 100f, 0, SpriteMeshType.FullRect, new Vector4(R, R, R, R));
            return roundedSprite;
        }

        static Text MakeText(Transform parent, Font font, int size, TextAnchor align, string value)
        {
            var go = new GameObject("Text", typeof(RectTransform), typeof(Text), typeof(Outline), typeof(Shadow));
            go.transform.SetParent(parent, false);
            var rt = (RectTransform)go.transform;
            rt.anchorMin = Vector2.zero; rt.anchorMax = Vector2.one;
            rt.offsetMin = rt.offsetMax = Vector2.zero;
            var t = go.GetComponent<Text>();
            t.font = font;
            t.fontSize = size;
            t.fontStyle = FontStyle.Bold;
            t.alignment = align;
            t.color = Color.white;
            t.text = value;
            t.horizontalOverflow = HorizontalWrapMode.Overflow;
            t.verticalOverflow = VerticalWrapMode.Overflow;
            go.GetComponent<Outline>().effectColor = new Color(0.35f, 0.05f, 0.45f, 0.9f);
            go.GetComponent<Outline>().effectDistance = new Vector2(3f, -3f);
            go.GetComponent<Shadow>().effectColor = new Color(0f, 0f, 0f, 0.35f);
            go.GetComponent<Shadow>().effectDistance = new Vector2(0f, -6f);
            return t;
        }

        public void ShowHint(bool show) { if (hintGo) hintGo.SetActive(show); }

        public void ShowComplete(bool show, int coins, int gems)
        {
            if (!completeGo) return;
            bool wasShown = completeGo.activeSelf;
            completeGo.SetActive(show);
            if (show) completeText.text = $"Fresh & Fluffy!\n<size=56>{coins} coins   {gems} gems</size>";
            completeText.supportRichText = true;
            if (show && !wasShown) completeAnim = 0f; // pop in
        }

        void Update()
        {
            float dt = Time.deltaTime;
            // banner pop: scale 0.6 -> 1.06 -> 1 with a quick alpha fade-in
            if (completeGo && completeGo.activeSelf && completeAnim < 1f)
            {
                completeAnim = Mathf.Min(1f, completeAnim + dt / 0.45f);
                float u = completeAnim;
                float s = u < 0.7f ? Mathf.Lerp(0.6f, 1.06f, Mathf.SmoothStep(0f, 1f, u / 0.7f)) : Mathf.Lerp(1.06f, 1f, (u - 0.7f) / 0.3f);
                completeGo.transform.localScale = Vector3.one * s;
                if (completeGroup) completeGroup.alpha = Mathf.Clamp01(u * 2.5f);
            }
            if (fadeImage)
            {
                fadeAlpha = Mathf.MoveTowards(fadeAlpha, fadeTarget, fadeSpeed * dt);
                fadeImage.color = new Color(FadeColor.r, FadeColor.g, FadeColor.b, fadeAlpha);
                bool on = fadeAlpha > 0.002f;
                if (fadeGo.activeSelf != on) fadeGo.SetActive(on);
            }
            if (items == null) return;
            if (items.Coins != shownCoins) { shownCoins = items.Coins; coinText.text = shownCoins.ToString(); coinPulse = 1f; }
            if (items.Gems != shownGems) { shownGems = items.Gems; gemText.text = shownGems.ToString(); gemPulse = 1f; }
            coinPulse = Mathf.Max(0f, coinPulse - Time.deltaTime * 4f);
            gemPulse = Mathf.Max(0f, gemPulse - Time.deltaTime * 4f);
            if (coinIcon) coinIcon.localScale = Vector3.one * (1f + coinPulse * 0.35f);
            if (gemIcon) gemIcon.localScale = Vector3.one * (1f + gemPulse * 0.35f);
        }
    }
}

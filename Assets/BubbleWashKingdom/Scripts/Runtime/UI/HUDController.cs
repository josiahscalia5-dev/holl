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
        GameObject hintGo, completeGo;
        int shownCoins = -1, shownGems = -1;
        float coinPulse, gemPulse;
        RectTransform coinIcon, gemIcon;

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
            hr.anchorMin = hr.anchorMax = new Vector2(0.5f, 0.18f);
            hr.sizeDelta = new Vector2(1000f, 160f);
            hintText = MakeText(hintGo.transform, font, 52, TextAnchor.MiddleCenter, "Swipe  ◀ ▶  to steer\nSwipe  ▲  to jump");

            completeGo = new GameObject("Complete", typeof(RectTransform));
            completeGo.transform.SetParent(canvasGo.transform, false);
            var cr = (RectTransform)completeGo.transform;
            cr.anchorMin = cr.anchorMax = new Vector2(0.5f, 0.72f);
            cr.sizeDelta = new Vector2(1000f, 320f);
            completeText = MakeText(completeGo.transform, font, 76, TextAnchor.MiddleCenter, "");
            completeGo.SetActive(false);
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
            completeGo.SetActive(show);
            if (show) completeText.text = $"Fresh & Fluffy!\n<size=56>{coins} coins   {gems} gems</size>";
            completeText.supportRichText = true;
        }

        void Update()
        {
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

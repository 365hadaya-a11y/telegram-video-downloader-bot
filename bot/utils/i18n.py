"""Lightweight bilingual i18n (العربية 🇸🇦 + English 🇬🇧).

Every user-facing string lives in :data:`_STRINGS` keyed by
``(language, key)``. Use :func:`t` to fetch a string and format it:

    >>> t("ar", "welcome", name="سارة")
    '✨ <b>بوت تحميل الفيديوهات</b> ...'

Languages: ``ar`` (default) and ``en``.
"""

from __future__ import annotations

LANG_AR = "ar"
LANG_EN = "en"
SUPPORTED_LANGS = (LANG_AR, LANG_EN)
DEFAULT_LANG = LANG_AR

# Human labels for the language picker keyboard.
LANG_LABELS = {
    LANG_AR: "🇸🇦 العربية",
    LANG_EN: "🇬🇧 English",
}

_LANG_NAMES = {
    LANG_AR: "العربية",
    LANG_EN: "English",
}


def normalize_lang(lang: str | None) -> str:
    """Coerce a raw language code into a supported one (default: ``ar``)."""
    if lang and lang.strip().lower() in SUPPORTED_LANGS:
        return lang.strip().lower()
    return DEFAULT_LANG


def lang_name(lang: str) -> str:
    return _LANG_NAMES.get(normalize_lang(lang), _LANG_NAMES[DEFAULT_LANG])


_STRINGS: dict[tuple[str, str], str] = {
    # ── /start welcome ─────────────────────────────────────────────
    (LANG_AR, "welcome"): (
        "✨ <b>بوت تحميل الفيديوهات</b> ✨\n\n"
        "👋 أهلاً بك، <b>{name}</b>!\n\n"
        "🎬 أستطيع تحميل الفيديوهات من <b>أكثر من 1000 موقع</b>:\n"
        "• يوتيوب ▶️\n"
        "• تيك توك 🎵\n"
        "• إنستغرام 📸\n"
        "• إكس / تويتر 🐦\n"
        "• …وغيرها الكثير 🌐\n\n"
        "⚡ <b>فقط أرسل لي رابط أي فيديو</b> وسأتكفل بالباقي!\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "💎 <b>المميزات</b>\n"
        "📥 تحميل بأعلى جودة\n"
        "📺 اختيار الجودة يدوياً\n"
        "🎧 استخراج الصوت (MP3)\n"
        "📊 شريط تقدم مباشر\n\n"
        "🌐 اللغة الحالية: <b>{lang_name}</b>\n"
        "💬 لتغيير اللغة استخدم /language\n\n"
        "🚀 <i>مدعوم بواسطة yt-dlp + FFmpeg</i>"
    ),
    (LANG_EN, "welcome"): (
        "✨ <b>Premium Video Downloader</b> ✨\n\n"
        "👋 Welcome, <b>{name}</b>!\n\n"
        "🎬 I can download videos from <b>1000+ websites</b>:\n"
        "• YouTube ▶️\n"
        "• TikTok 🎵\n"
        "• Instagram 📸\n"
        "• X / Twitter 🐦\n"
        "• …and many more 🌐\n\n"
        "⚡ <b>Just send me any video link</b> and I'll handle the rest!\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "💎 <b>Features</b>\n"
        "📥 Best-quality downloads\n"
        "📺 Manual quality selection\n"
        "🎧 Audio extraction (MP3)\n"
        "📊 Real-time progress bar\n\n"
        "🌐 Current language: <b>{lang_name}</b>\n"
        "💬 Use /language to change it\n\n"
        "🚀 <i>Powered by yt-dlp + FFmpeg</i>"
    ),

    # ── /help ──────────────────────────────────────────────────────
    (LANG_AR, "help"): (
        "❓ <b>طريقة الاستخدام</b>\n\n"
        "1️⃣ أرسل لي رابط فيديو\n"
        "2️⃣ اختر خيار الجودة\n"
        "3️⃣ استمتع بملفك! 🎉\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "<b>الأوامر</b>\n"
        "/start — تشغيل البوت\n"
        "/help — عرض المساعدة\n"
        "/language — تغيير اللغة 🌐\n"
        "/cancel — إلغاء التحميل الحالي\n\n"
        "💡 <i>نصيحة: يمكنك الإلغاء في أي وقت بزر ❌.</i>"
    ),
    (LANG_EN, "help"): (
        "❓ <b>How to use</b>\n\n"
        "1️⃣ Send me a video URL\n"
        "2️⃣ Pick a quality option\n"
        "3️⃣ Enjoy your file! 🎉\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "<b>Commands</b>\n"
        "/start — Start the bot\n"
        "/help — Show this help\n"
        "/language — Change language 🌐\n"
        "/cancel — Cancel the current download\n\n"
        "💡 <i>Tip: you can cancel anytime with the ❌ button.</i>"
    ),

    # ── /language ──────────────────────────────────────────────────
    (LANG_AR, "language_prompt"): "🌐 <b>اختر لغتك المفضلة</b> 👇",
    (LANG_EN, "language_prompt"): "🌐 <b>Choose your preferred language</b> 👇",
    (LANG_AR, "language_changed"): "✅ تم تغيير اللغة إلى <b>العربية</b> 🇸🇦",
    (LANG_EN, "language_changed"): "✅ Language changed to <b>English</b> 🇬🇧",

    # ── /cancel ────────────────────────────────────────────────────
    (LANG_AR, "cancel_started"): "🚫 <b>جاري إلغاء التحميل…</b>",
    (LANG_EN, "cancel_started"): "🚫 <b>Cancelling your download…</b>",
    (LANG_AR, "cancel_nothing"): "😊 <b>لا يوجد شيء لإلغائه</b> — ليس لديك تحميلات نشطة.",
    (LANG_EN, "cancel_nothing"): "😊 <b>Nothing to cancel</b> — you have no active downloads.",

    # ── URL detection ──────────────────────────────────────────────
    (LANG_AR, "no_url"): (
        "🤔 <b>لم أجد رابط فيديو</b> في رسالتك.\n\n"
        "🔗 أرسل لي رابطاً صحيحاً، مثلاً:\n"
        "<code>https://youtube.com/watch?v=…</code>\n\n"
        "💡 استخدم /help إذا احتجت مساعدة."
    ),
    (LANG_EN, "no_url"): (
        "🤔 <b>I couldn't find a video link</b> in your message.\n\n"
        "🔗 Send me a valid URL, e.g.\n"
        "<code>https://youtube.com/watch?v=…</code>\n\n"
        "💡 Use /help if you need a hand."
    ),
    (LANG_AR, "unknown_command"): "❓ <b>أمر غير معروف.</b>\nاستخدم /help لمعرفة ما يمكنني فعله.",
    (LANG_EN, "unknown_command"): "❓ <b>Unknown command.</b>\nUse /help to see what I can do.",
    (LANG_AR, "group_only"): "🔒 <b>من فضلك استخدم البوت في محادثة خاصة</b> لتحميل الفيديوهات. 😊",
    (LANG_EN, "group_only"): "🔒 <b>Please use me in a private chat</b> to download videos. 😊",

    # ── Download flow ──────────────────────────────────────────────
    (LANG_AR, "active_download"): (
        "⏳ <b>لديك تحميل نشط بالفعل!</b>\n"
        "استخدم زر ❌ <b>إلغاء</b> أو /cancel لإيقافه أولاً."
    ),
    (LANG_EN, "active_download"): (
        "⏳ <b>You already have an active download!</b>\n"
        "Use the ❌ <b>Cancel</b> button or /cancel to stop it first."
    ),
    (LANG_AR, "daily_limit"): (
        "🚦 <b>تم الوصول للحد اليومي.</b>\n"
        "لقد استخدمت <b>{limit}</b> تحميلاً لليوم. عُد غداً! 🌙"
    ),
    (LANG_EN, "daily_limit"): (
        "🚦 <b>Daily limit reached.</b>\n"
        "You've used your <b>{limit}</b> downloads for today. Come back tomorrow! 🌙"
    ),
    (LANG_AR, "fetching"): "🔍 <b>جاري جلب معلومات الفيديو…</b>",
    (LANG_EN, "fetching"): "🔍 <b>Fetching video information…</b>",
    (LANG_AR, "retry_info"): "🔄 <b>جاري جلب المعلومات…</b>\nمحاولة {attempt}/{total}",
    (LANG_EN, "retry_info"): "🔄 <b>Fetching info…</b>\nRetry {attempt}/{total}",
    (LANG_AR, "session_expired"): "⏳ انتهت صلاحية هذه الجلسة — أرسل رابطاً جديداً!",
    (LANG_EN, "session_expired"): "⏳ This session has expired — send a new link!",
    (LANG_AR, "cancelling"): "🚫 جاري الإلغاء…",
    (LANG_EN, "cancelling"): "🚫 Cancelling…",

    # ── Info card ──────────────────────────────────────────────────
    (LANG_AR, "info_card"): (
        "🎬 <b>تم العثور على الفيديو!</b>\n\n"
        "{title}\n"
        "👤 <b>القناة:</b> {channel}\n"
        "⏱️ <b>المدة:</b> {duration}\n"
        "📦 <b>الحجم:</b> ~{size}\n"
        "📺 <b>أقصى جودة:</b> {height}p\n\n"
        "💡 <b>اختر خياراً أدناه:</b>"
    ),
    (LANG_EN, "info_card"): (
        "🎬 <b>Video Found!</b>\n\n"
        "{title}\n"
        "👤 <b>Channel:</b> {channel}\n"
        "⏱️ <b>Duration:</b> {duration}\n"
        "📦 <b>Size:</b> ~{size}\n"
        "📺 <b>Max quality:</b> {height}p\n\n"
        "💡 <b>Choose an option below:</b>"
    ),
    (LANG_AR, "info_untitled"): "بدون عنوان",
    (LANG_EN, "info_untitled"): "Untitled",
    (LANG_AR, "info_unknown"): "غير معروف",
    (LANG_EN, "info_unknown"): "Unknown",

    # ── Progress captions ──────────────────────────────────────────
    (LANG_AR, "downloading"): "⬇️ <b>جاري التحميل…</b>",
    (LANG_EN, "downloading"): "⬇️ <b>Downloading…</b>",
    (LANG_AR, "downloading_wait"): "⏳ <i>جاري التحميل…</i>",
    (LANG_EN, "downloading_wait"): "⏳ <i>Downloading…</i>",
    (LANG_AR, "dl_hint"): "💎 <i>قد يستغرق هذا بعض الوقت للملفات الكبيرة.</i>",
    (LANG_EN, "dl_hint"): "💎 <i>This may take a while for large files.</i>",
    (LANG_AR, "processing"): "🎬 <b>جاري معالجة الفيديو…</b>\n⚙️ دمج الصوت والفيديو باستخدام FFmpeg…",
    (LANG_EN, "processing"): "🎬 <b>Processing video…</b>\n⚙️ Merging audio & video with FFmpeg…",
    (LANG_AR, "queued"): (
        "⏳ <b>أنت في قائمة الانتظار!</b>\n\n"
        "الموقع: <b>#{position}</b>\n"
        "🧵 عدد العمال المتاحين: <b>{workers}</b>\n\n"
        "سيبدأ تحميلك تلقائياً. 🚀"
    ),
    (LANG_EN, "queued"): (
        "⏳ <b>You're in the download queue!</b>\n\n"
        "Position: <b>#{position}</b>\n"
        "🧵 <b>{workers}</b> worker(s) available\n\n"
        "Your download will start automatically. 🚀"
    ),
    (LANG_AR, "uploading"): "📤 <b>جاري الرفع إلى تيليجرام…</b>",
    (LANG_EN, "uploading"): "📤 <b>Uploading to Telegram…</b>",
    (LANG_AR, "almost_there"): "🚀 أوشكنا على الانتهاء!",
    (LANG_EN, "almost_there"): "🚀 Almost there!",
    (LANG_AR, "finalising"): "📤 <b>جاري إنهاء الرفع…</b>\n\nقد يستغرق هذا لحظة للملفات الكبيرة. ⏳",
    (LANG_EN, "finalising"): "📤 <b>Finalising upload…</b>\n\nThis may take a moment for large files. ⏳",
    (LANG_AR, "retry_download"): (
        "🔄 <b>جاري إعادة محاولة التحميل…</b> ({attempt}/{total})\n\n"
        "🌐 حدث خطأ في الشبكة. انتظر قليلاً!"
    ),
    (LANG_EN, "retry_download"): (
        "🔄 <b>Retrying download…</b> ({attempt}/{total})\n\n"
        "🌐 A network error occurred. Hang tight!"
    ),

    # ── Success / delivered ────────────────────────────────────────
    (LANG_AR, "success"): "✅ <b>اكتمل التحميل!</b>",
    (LANG_EN, "success"): "✅ <b>Download complete!</b>",
    (LANG_AR, "duration_label"): "⏱️ المدة",
    (LANG_EN, "duration_label"): "Duration",
    (LANG_AR, "size_label"): "📦 الحجم",
    (LANG_EN, "size_label"): "📦 Size",
    (LANG_AR, "format_audio"): "🎧 الصيغة: MP3",
    (LANG_EN, "format_audio"): "🎧 Format: MP3",
    (LANG_AR, "quality_label"): "🎞️ الجودة: {height}p",
    (LANG_EN, "quality_label"): "🎞️ Quality: {height}p",
    (LANG_AR, "quality_best"): "🎞️ الجودة: الأفضل",
    (LANG_EN, "quality_best"): "🎞️ Quality: Best",
    (LANG_AR, "thanks"): "✨ شكراً لاستخدامك <b>بوت التحميل</b>!",
    (LANG_EN, "thanks"): "✨ Thanks for using <b>Premium Downloader</b>!",
    (LANG_AR, "delivered"): (
        "🎉 <b>تم التسليم!</b>\n"
        "📤 انتهى الرفع خلال <b>{elapsed:.1f}s</b>\n"
        "📦 {size}\n\n"
        "🚀 استمتع بالفيديو!"
    ),
    (LANG_EN, "delivered"): (
        "🎉 <b>Delivered!</b>\n"
        "📤 Upload finished in <b>{elapsed:.1f}s</b>\n"
        "📦 {size}\n\n"
        "🚀 Enjoy your video!"
    ),

    # ── Cancelled / errors ─────────────────────────────────────────
    (LANG_AR, "cancelled"): "🚫 <b>تم إلغاء التحميل.</b>\n😊 لا مشكلة — أرسل رابطاً جديداً في أي وقت!",
    (LANG_EN, "cancelled"): "🚫 <b>Download cancelled.</b>\n😊 No problem — send a new link anytime!",
    (LANG_AR, "error_card"): (
        "❌ <b>فشل التحميل</b>\n\n"
        "{reason}\n\n"
        "💡 <b>نصائح:</b>\n"
        "• تأكد أن الفيديو عام\n"
        "• راجع كتابة الرابط\n"
        "• حاول مجدداً بعد قليل"
    ),
    (LANG_EN, "error_card"): (
        "❌ <b>Download failed</b>\n\n"
        "{reason}\n\n"
        "💡 <b>Tips:</b>\n"
        "• Make sure the video is public\n"
        "• Check the URL spelling\n"
        "• Try again in a few minutes"
    ),
    (LANG_AR, "too_large"): (
        "⚠️ <b>الملف كبير جداً</b>\n\n"
        "هذا الملف بحجم <b>{size}</b>، وهو يتجاوز حد "
        "<b>{limit_mb} م.ب</b>.\n\n"
        "جرّب جودة أقل أو الصوت فقط. 💡"
    ),
    (LANG_EN, "too_large"): (
        "⚠️ <b>File too large</b>\n\n"
        "This file is <b>{size}</b>, which exceeds the "
        "<b>{limit_mb} MB</b> limit.\n\n"
        "Try a lower quality or audio-only instead. 💡"
    ),
    (LANG_AR, "too_large_warn"): (
        "⚠️ <b>هذا الملف كبير جداً!</b>\n\n"
        "الحجم المقدر: <b>{size}</b>\n"
        "الحد: <b>{limit_mb} م.ب</b>\n\n"
        "اختر جودة أصغر أو حمّل الصوت بدلاً من ذلك."
    ),
    (LANG_EN, "too_large_warn"): (
        "⚠️ <b>This file is too large!</b>\n\n"
        "Estimated size: <b>{size}</b>\n"
        "Limit: <b>{limit_mb} MB</b>\n\n"
        "Pick a smaller quality or grab the audio instead."
    ),
    (LANG_AR, "telegram_rejected"): (
        "⚠️ <b>تيليجرام رفض الملف.</b>\n\n"
        "واجهة برمجة التطبيقات القياسية تسمح برفع حتى <b>50 م.ب</b> فقط.\n"
        "جرّب جودة أقل أو الصوت فقط أو خادم Bot API محلي."
    ),
    (LANG_EN, "telegram_rejected"): (
        "⚠️ <b>Telegram rejected the file.</b>\n\n"
        "The standard Bot API only allows uploads up to <b>50 MB</b>.\n"
        "Try a lower quality, audio-only, or a local Bot API server."
    ),

    # ── Friendly errors ────────────────────────────────────────────
    (LANG_AR, "err_cancelled"): "🚫 <b>تم الإلغاء.</b>",
    (LANG_EN, "err_cancelled"): "🚫 <b>Cancelled.</b>",
    (LANG_AR, "err_private"): "🔒 <b>هذا الفيديو خاص.</b>",
    (LANG_EN, "err_private"): "🔒 <b>This video is private.</b>",
    (LANG_AR, "err_login"): "🔐 <b>هذا الفيديو يتطلب تسجيل الدخول.</b>\nأضف ملف كوكيز (<code>COOKIES_FILE</code>) وحاول مجدداً.",
    (LANG_EN, "err_login"): "🔐 <b>This video requires login.</b>\nAdd a cookies file (<code>COOKIES_FILE</code>) and retry.",
    (LANG_AR, "err_age"): "🔞 <b>المحتوى المقيّد عمرياً غير مدعوم.</b>",
    (LANG_EN, "err_age"): "🔞 <b>Age-restricted content isn't supported.</b>",
    (LANG_AR, "err_network"): "🌐 <b>خطأ في الشبكة.</b>\nحاول مجدداً بعد بضع دقائق.",
    (LANG_EN, "err_network"): "🌐 <b>Network error.</b>\nPlease try again in a few minutes.",
    (LANG_AR, "err_unsupported"): "❓ <b>هذا الموقع غير مدعوم.</b>",
    (LANG_EN, "err_unsupported"): "❓ <b>This website is not supported.</b>",
    (LANG_AR, "err_unavailable"): "🗑️ <b>الفيديو غير متاح أو تم حذفه.</b>",
    (LANG_EN, "err_unavailable"): "🗑️ <b>The video is unavailable or was removed.</b>",
    (LANG_AR, "err_generic"): "⚠️ <b>حدث خطأ ما أثناء جلب الفيديو.</b>",
    (LANG_EN, "err_generic"): "⚠️ <b>Something went wrong while fetching the video.</b>",
    (LANG_AR, "err_unhandled"): "⚠️ <b>حدث خطأ ما.</b>\nحاول مجدداً لاحقاً.",
    (LANG_EN, "err_unhandled"): "⚠️ <b>Something went wrong.</b>\nPlease try again later.",

    # ── Quality menu ───────────────────────────────────────────────
    (LANG_AR, "choose_quality"): "📺 <b>اختر جودة الفيديو</b>\n\nاختر دقة من الأسفل 👇",
    (LANG_EN, "choose_quality"): "📺 <b>Choose video quality</b>\n\nSelect a resolution below 👇",

    # ── Forced subscription (الاشتراك الإجباري) ────────────────────
    (LANG_AR, "join_message"): (
        "🔒 <b>الاشتراك بالقناة مطلوب</b>\n\n"
        "لاستخدام البوت، يرجى الانضمام إلى قناتنا أولاً:\n"
        "👉 <b>{channel}</b>\n\n"
        "ثم اضغط الزر أدناه للتحقق. ✅"
    ),
    (LANG_EN, "join_message"): (
        "🔒 <b>Channel subscription required</b>\n\n"
        "To use the bot, please join our channel first:\n"
        "👉 <b>{channel}</b>\n\n"
        "Then press the button below to verify. ✅"
    ),
    (LANG_AR, "join_channel_btn"): "🔗 الانضمام للقناة",
    (LANG_EN, "join_channel_btn"): "🔗 Join Channel",
    (LANG_AR, "joined_btn"): "✅ انضممت",
    (LANG_EN, "joined_btn"): "✅ I've Joined",
    (LANG_AR, "access_granted"): (
        "✅ <b>تم منح الوصول!</b>\n\n"
        "أنت الآن عضو في القناة. 🎉\n"
        "أرسل لي رابط الفيديو ولنبدأ! 🎬"
    ),
    (LANG_EN, "access_granted"): (
        "✅ <b>Access granted!</b>\n\n"
        "You're a member of the channel now. 🎉\n"
        "Send me your video link and let's go! 🎬"
    ),
    (LANG_AR, "not_joined"): "❌ ليس بعد — يرجى الانضمام إلى القناة أولاً!",
    (LANG_EN, "not_joined"): "❌ Not yet — please join the channel first!",
    (LANG_AR, "join_welcome"): "🎉 أهلاً بك!",
    (LANG_EN, "join_welcome"): "🎉 Welcome!",

    # ── Admin ──────────────────────────────────────────────────────
    (LANG_AR, "admins_only"): "⛔ <b>للمشرفين فقط.</b>\nهذا الأمر مقيّد على مالك البوت.",
    (LANG_EN, "admins_only"): "⛔ <b>Admins only.</b>\nThis command is restricted to the bot owner.",
    (LANG_AR, "stats"): (
        "📊 <b>إحصائيات البوت</b>\n\n"
        "👥 المستخدمون: <b>{users}</b>\n"
        "✅ إجمالي التحميلات: <b>{total}</b>\n"
        "📅 تحميلات اليوم: <b>{today}</b>\n"
        "⚙️ الجلسات النشطة: <b>{active}</b>\n"
        "⏳ في قائمة الانتظار: <b>{queued}</b>\n"
        "🗑️ استخدام الملفات المؤقتة: <b>{temp_size}</b>\n\n"
        "🧵 العمال: <b>{workers}</b>\n"
        "🚦 الحد اليومي/مستخدم: <b>{limit}</b>"
    ),
    (LANG_EN, "stats"): (
        "📊 <b>Bot Statistics</b>\n\n"
        "👥 Users: <b>{users}</b>\n"
        "✅ Total downloads: <b>{total}</b>\n"
        "📅 Downloads today: <b>{today}</b>\n"
        "⚙️ Active sessions: <b>{active}</b>\n"
        "⏳ Queued downloads: <b>{queued}</b>\n"
        "🗑️ Temp usage: <b>{temp_size}</b>\n\n"
        "🧵 Workers: <b>{workers}</b>\n"
        "🚦 Daily limit/user: <b>{limit}</b>"
    ),
    (LANG_AR, "setsticker_usage"): (
        "🎨 <b>الاستخدام:</b> أجب على ملصق بـ\n"
        "<code>/setsticker {keys}</code>\n\n"
        "مثال:\n<code>/setsticker welcome</code>"
    ),
    (LANG_EN, "setsticker_usage"): (
        "🎨 <b>Usage:</b> reply to a sticker with\n"
        "<code>/setsticker {keys}</code>\n\n"
        "Example:\n<code>/setsticker welcome</code>"
    ),
    (LANG_AR, "reply_sticker"): "ℹ️ <b>أجب على ملصق</b> بهذا الأمر لحفظه.",
    (LANG_EN, "reply_sticker"): "ℹ️ <b>Reply to a sticker</b> with this command to save it.",
    (LANG_AR, "sticker_saved"): "✅ تم حفظ الملصق <b>{key}</b>! سيُستخدم من الآن فصاعداً. ✨",
    (LANG_EN, "sticker_saved"): "✅ Sticker <b>{key}</b> saved! It will be used from now on. ✨",
    (LANG_AR, "resetsticker_usage"): "🎨 الاستخدام: <code>/resetsticker {keys}</code>",
    (LANG_EN, "resetsticker_usage"): "🎨 Usage: <code>/resetsticker {keys}</code>",
    (LANG_AR, "sticker_reset"): "🗑️ تم إرجاع الملصق <b>{key}</b> للسلوك الافتراضي.",
    (LANG_EN, "sticker_reset"): "🗑️ Sticker <b>{key}</b> reset to default behaviour.",
    (LANG_AR, "broadcast_running"): "📣 البث قيد التشغيل بالفعل. انتظر حتى ينتهي أو اضغط 🛑 إيقاف.",
    (LANG_AR, "broadcast_stop_btn"): "🛑 جاري إيقاف البث…",
    (LANG_EN, "broadcast_stop_btn"): "🛑 Stopping broadcast…",
    (LANG_EN, "broadcast_running"): "📣 A broadcast is already running. Wait for it to finish or press 🛑 Stop.",
    (LANG_AR, "broadcast_usage"): (
        "📣 <b>الاستخدام:</b>\n"
        "<code>/broadcast &lt;نص&gt;</code> — بث رسالة نصية\n"
        "<code>/broadcast</code> <i>(أجب على صورة/فيديو/ملف)</i> — بث وسائط\n\n"
        "ستُرسل إلى <b>كل مستخدم</b> شغّل البوت."
    ),
    (LANG_EN, "broadcast_usage"): (
        "📣 <b>Usage:</b>\n"
        "<code>/broadcast &lt;text&gt;</code> — announce a text message\n"
        "<code>/broadcast</code> <i>(reply to a photo/video/file)</i> — announce media\n\n"
        "It will be sent to <b>every user</b> who started the bot."
    ),
    (LANG_AR, "broadcasting"): "📣 <b>جاري البث…</b>\n\n⏳ التحضير…",
    (LANG_EN, "broadcasting"): "📣 <b>Broadcasting…</b>\n\n⏳ Preparing…",
    (LANG_AR, "broadcast_progress"): (
        "📣 <b>جاري البث…</b>\n\n"
        "✅ تم الإرسال: <b>{sent}</b>\n"
        "❌ فشل: <b>{failed}</b>\n"
        "🚫 محظور: <b>{blocked}</b>\n\n"
        "⏳ {done}/{total}"
    ),
    (LANG_EN, "broadcast_progress"): (
        "📣 <b>Broadcasting…</b>\n\n"
        "✅ Sent: <b>{sent}</b>\n"
        "❌ Failed: <b>{failed}</b>\n"
        "🚫 Blocked: <b>{blocked}</b>\n\n"
        "⏳ {done}/{total}"
    ),
    (LANG_AR, "broadcast_crashed"): "⚠️ <b>تعطل البث.</b>\nحدث خطأ غير متوقع أثناء الإرسال.",
    (LANG_EN, "broadcast_crashed"): "⚠️ <b>Broadcast crashed.</b>\nAn unexpected error interrupted the announcement.",
    (LANG_AR, "broadcast_stopped"): "🛑 <b>تم إيقاف البث.</b>\n\n",
    (LANG_EN, "broadcast_stopped"): "🛑 <b>Broadcast stopped.</b>\n\n",
    (LANG_AR, "broadcast_finished"): "✅ <b>انتهى البث!</b>\n\n",
    (LANG_EN, "broadcast_finished"): "✅ <b>Broadcast finished!</b>\n\n",
    (LANG_AR, "broadcast_summary"): (
        "📨 تم الإرسال: <b>{sent}</b>\n"
        "❌ فشل: <b>{failed}</b>\n"
        "🚫 محظور وأُزيل: <b>{blocked}</b>"
    ),
    (LANG_EN, "broadcast_summary"): (
        "📨 Sent: <b>{sent}</b>\n"
        "❌ Failed: <b>{failed}</b>\n"
        "🚫 Blocked & removed: <b>{blocked}</b>"
    ),
    (LANG_AR, "no_stickers"): (
        "🎨 <b>لم يتم إعداد ملصقات بعد.</b>\n"
        "أجب على ملصق بـ <code>/setsticker &lt;key&gt;</code> لتعيين واحد.\n\n"
        "المفاتيح المتاحة: <code>{keys}</code>"
    ),
    (LANG_EN, "no_stickers"): (
        "🎨 <b>No stickers configured yet.</b>\n"
        "Reply to a sticker with <code>/setsticker &lt;key&gt;</code> to assign one.\n\n"
        "Available keys: <code>{keys}</code>"
    ),
    (LANG_AR, "sticker_mapping"): "🎨 <b>خريطة الملصقات</b>\n",
    (LANG_EN, "sticker_mapping"): "🎨 <b>Sticker mapping</b>\n",
    (LANG_AR, "sticker_set"): "✅ مضبوط",
    (LANG_EN, "sticker_set"): "✅ set",
    (LANG_AR, "sticker_not_set"): "— غير مضبوط",
    (LANG_EN, "sticker_not_set"): "— not set",

    # ── Button labels ──────────────────────────────────────────────
    (LANG_AR, "btn_best"): "🎥 أفضل جودة",
    (LANG_EN, "btn_best"): "🎥 Best Quality",
    (LANG_AR, "btn_choose"): "📺 اختر الجودة",
    (LANG_EN, "btn_choose"): "📺 Choose Quality",
    (LANG_AR, "btn_audio"): "🎵 الصوت فقط",
    (LANG_EN, "btn_audio"): "🎵 Audio Only",
    (LANG_AR, "btn_cancel"): "❌ إلغاء",
    (LANG_EN, "btn_cancel"): "❌ Cancel",
    (LANG_AR, "btn_main"): "🔙 الرئيسية",
    (LANG_EN, "btn_main"): "🔙 Main",
    (LANG_AR, "btn_stop_broadcast"): "🛑 إيقاف البث",
    (LANG_EN, "btn_stop_broadcast"): "🛑 Stop Broadcast",
    (LANG_AR, "welcome_help_btn"): "❓ المساعدة",
    (LANG_EN, "welcome_help_btn"): "❓ Help",

    # ── Forced subscription (multi-channel) ───────────────────────
    (LANG_AR, "join_message_title"): "🔒 <b>الاشتراك بالقنوات مطلوب</b>\n\nلاستخدام البوت، يرجى الانضمام إلى <b>كل</b> القنوات التالية أولاً:",
    (LANG_EN, "join_message_title"): "🔒 <b>Channel subscription required</b>\n\nTo use the bot, please join <b>all</b> of these channels first:",
    (LANG_AR, "join_message_footer"): "ثم اضغط الزر أدناه للتحقق. ✅",
    (LANG_EN, "join_message_footer"): "Then press the button below to verify. ✅",
    (LANG_AR, "join_channel_btn"): "🔗 انضم {channel}",
    (LANG_EN, "join_channel_btn"): "🔗 Join {channel}",
    (LANG_AR, "still_missing"): "❌ ما زلت لم تنضم إلى القناة: <b>{channels}</b>\n\nانضم أولاً ثم أعد المحاولة. 🔄",
    (LANG_EN, "still_missing"): "❌ You still haven't joined: <b>{channels}</b>\n\nJoin them first, then try again. 🔄",

    # ── Admin panel (لوحة تحكم المدير) ────────────────────────────
    (LANG_AR, "panel_title"): "🛠️ <b>لوحة تحكم المدير</b>\n\nاختر قسماً من الأزرار أدناه 👇",
    (LANG_EN, "panel_title"): "🛠️ <b>Admin Control Panel</b>\n\nPick a section from the buttons below 👇",
    (LANG_AR, "panel_btn_stats"): "📊 الإحصائيات",
    (LANG_EN, "panel_btn_stats"): "📊 Statistics",
    (LANG_AR, "panel_btn_users"): "👥 المستخدمون",
    (LANG_EN, "panel_btn_users"): "👥 Users",
    (LANG_AR, "panel_btn_broadcast"): "📣 البث",
    (LANG_EN, "panel_btn_broadcast"): "📣 Broadcast",
    (LANG_AR, "panel_btn_stickers"): "🎨 الملصقات",
    (LANG_EN, "panel_btn_stickers"): "🎨 Stickers",
    (LANG_AR, "panel_btn_channels"): "🔒 القنوات",
    (LANG_EN, "panel_btn_channels"): "🔒 Channels",
    (LANG_AR, "panel_btn_settings"): "⚙️ الإعدادات",
    (LANG_EN, "panel_btn_settings"): "⚙️ Settings",
    (LANG_AR, "panel_btn_language"): "🌐 اللغة",
    (LANG_EN, "panel_btn_language"): "🌐 Language",
    (LANG_AR, "panel_btn_close"): "❌ إغلاق",
    (LANG_EN, "panel_btn_close"): "❌ Close",
    (LANG_AR, "panel_btn_back"): "🔙 رجوع",
    (LANG_EN, "panel_btn_back"): "🔙 Back",
    (LANG_AR, "panel_btn_refresh"): "🔄 تحديث",
    (LANG_EN, "panel_btn_refresh"): "🔄 Refresh",
    (LANG_AR, "panel_btn_add_channel"): "➕ إضافة قناة",
    (LANG_EN, "panel_btn_add_channel"): "➕ Add channel",
    (LANG_AR, "panel_closed"): "🛠️ تم إغلاق لوحة التحكم.\nافتحها مجدداً بـ /panel",
    (LANG_EN, "panel_closed"): "🛠️ Panel closed.\nReopen it with /panel",
    (LANG_AR, "panel_admins_only"): "⛔ <b>للمشرفين فقط.</b>\nلوحة التحكم متاحة لمالك البوت.",
    (LANG_EN, "panel_admins_only"): "⛔ <b>Admins only.</b>\nThe panel is restricted to the bot owner.",
    (LANG_AR, "panel_users_title"): "👥 <b>المستخدمون</b>\n\nالإجمالي: <b>{total}</b>\nأكثر الأعضاء تحميلاً:",
    (LANG_EN, "panel_users_title"): "👥 <b>Users</b>\n\nTotal: <b>{total}</b>\nTop downloaders:",
    (LANG_AR, "panel_users_empty"): "👥 <b>المستخدمون</b>\n\nالإجمالي: <b>{total}</b>\n\nلا توجد تحميلات ناجحة بعد. 📭",
    (LANG_EN, "panel_users_empty"): "👥 <b>Users</b>\n\nTotal: <b>{total}</b>\n\nNo successful downloads yet. 📭",
    (LANG_AR, "panel_broadcast_title"): "📣 <b>البث الجماعي</b>\n\n<code>/broadcast &lt;نص&gt;</code> — بث رسالة نصية\n<code>/broadcast</code> <i>(أجب على صورة/فيديو/ملف)</i> — بث وسائط\n\nتُرسل إلى كل مستخدم شغّل البوت.",
    (LANG_EN, "panel_broadcast_title"): "📣 <b>Broadcast</b>\n\n<code>/broadcast &lt;text&gt;</code> — announce a text message\n<code>/broadcast</code> <i>(reply to a photo/video/file)</i> — announce media\n\nSent to every user who started the bot.",
    (LANG_AR, "panel_channels_title"): "🔒 <b>القنوات الإجبارية</b>\n\n{channels}\n\n• للإضافة: <code>/setchannel @channel</code>\n• للحذف: اضغط زر القناة أدناه",
    (LANG_EN, "panel_channels_title"): "🔒 <b>Forced channels</b>\n\n{channels}\n\n• To add: <code>/setchannel @channel</code>\n• To remove: tap a channel below",
    (LANG_AR, "panel_channels_empty"): "🔒 <b>القنوات الإجبارية</b>\n\nلا توجد قنوات مفعّلة حالياً.\nأضف قناة عبر: <code>/setchannel @channel</code>",
    (LANG_EN, "panel_channels_empty"): "🔒 <b>Forced channels</b>\n\nNo channels configured yet.\nAdd one with: <code>/setchannel @channel</code>",
    (LANG_AR, "panel_settings_title"): "⚙️ <b>الإعدادات</b>\n\n{lines}",
    (LANG_EN, "panel_settings_title"): "⚙️ <b>Settings</b>\n\n{lines}",
    (LANG_AR, "panel_stickers_title"): "🎨 <b>خريطة الملصقات</b>\n\n{lines}",
    (LANG_EN, "panel_stickers_title"): "🎨 <b>Sticker mapping</b>\n\n{lines}",
    (LANG_AR, "setchannel_usage"): "🔒 الاستخدام: <code>/setchannel @channel</code>\nمثال: <code>/setchannel @MyAnnouncements</code>",
    (LANG_EN, "setchannel_usage"): "🔒 Usage: <code>/setchannel @channel</code>\nExample: <code>/setchannel @MyAnnouncements</code>",
    (LANG_AR, "setchannel_added"): "✅ تمت إضافة القناة <b>{channel}</b>!\nالآن يجب على المستخدمين الانضمام إليها أيضاً.",
    (LANG_EN, "setchannel_added"): "✅ Channel <b>{channel}</b> added!\nUsers must now join it too.",
    (LANG_AR, "setchannel_dup"): "ℹ️ القناة <b>{channel}</b> مفعّلة مسبقاً.",
    (LANG_EN, "setchannel_dup"): "ℹ️ Channel <b>{channel}</b> is already active.",
    (LANG_AR, "delchannel_removed"): "🗑️ تمت إزالة القناة <b>{channel}</b> من الاشتراك الإجباري.",
    (LANG_EN, "delchannel_removed"): "🗑️ Channel <b>{channel}</b> removed from forced subscription.",
    (LANG_AR, "delchannel_missing"): "❓ القناة <b>{channel}</b> غير موجودة في القائمة.",
    (LANG_EN, "delchannel_missing"): "❓ Channel <b>{channel}</b> is not in the list.",
    (LANG_AR, "delchannel_env_protected"): "🔒 القناة <b>{channel}</b> مضبوطة من ملف الإعدادات ولا يمكن حذفها من هنا. عدّل <code>FORCE_CHANNELS</code> بدلاً من ذلك.",
    (LANG_EN, "delchannel_env_protected"): "🔒 Channel <b>{channel}</b> comes from the config file and can't be removed here. Edit <code>FORCE_CHANNELS</code> instead.",
    (LANG_AR, "channel_env_note"): "(من الإعدادات)",
    (LANG_EN, "channel_env_note"): "(from config)",

    # ── Bot command descriptions ───────────────────────────────────
    (LANG_AR, "cmd_start"): "🚀 تشغيل البوت",
    (LANG_EN, "cmd_start"): "🚀 Start the bot",
    (LANG_AR, "cmd_help"): "❓ المساعدة",
    (LANG_EN, "cmd_help"): "❓ Help",
    (LANG_AR, "cmd_cancel"): "🚫 إلغاء التحميل الحالي",
    (LANG_EN, "cmd_cancel"): "🚫 Cancel current download",
    (LANG_AR, "cmd_language"): "🌐 تغيير اللغة",
    (LANG_EN, "cmd_language"): "🌐 Change language",
    (LANG_AR, "cmd_panel"): "🛠️ لوحة تحكم المدير",
    (LANG_EN, "cmd_panel"): "🛠️ Admin panel",
    (LANG_AR, "cmd_broadcast"): "📣 بث إعلان",
    (LANG_EN, "cmd_broadcast"): "📣 Broadcast announcement",
    (LANG_AR, "cmd_stats"): "📊 إحصائيات البوت",
    (LANG_EN, "cmd_stats"): "📊 Bot statistics",
    (LANG_AR, "cmd_stickers"): "🎨 خريطة الملصقات",
    (LANG_EN, "cmd_stickers"): "🎨 Sticker mapping",
    (LANG_AR, "cmd_setsticker"): "🎨 تعيين ملصق",
    (LANG_EN, "cmd_setsticker"): "🎨 Set a flow sticker",
    (LANG_AR, "cmd_setchannel"): "🔒 إضافة قناة إجبارية",
    (LANG_EN, "cmd_setchannel"): "🔒 Add forced channel",
    (LANG_AR, "cmd_delchannel"): "🔒 حذف قناة إجبارية",
    (LANG_EN, "cmd_delchannel"): "🔒 Remove forced channel",
}


def t(lang: str, key: str, **kwargs: object) -> str:
    """Return the string for ``key`` in ``lang`` with placeholders filled.

    Falls back to Arabic, then to the key itself, so a missing
    translation never crashes the bot.
    """
    text = _STRINGS.get((normalize_lang(lang), key))
    if text is None:
        text = _STRINGS.get((DEFAULT_LANG, key), key)
    try:
        return text.format(**kwargs)
    except (KeyError, IndexError):
        return text

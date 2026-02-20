"""
監視対象チャンネルリスト
チャンネルの追加・削除はこのファイルを編集するだけでOK。

各チャンネルには以下の情報を持たせる:
- handle: YouTubeハンドル (@xxx)
- channel_id: YouTubeチャンネルID (UC...)
- name: 表示名
- tier: 分類
- note: メモ（企画参考ポイントなど）

channel_id は初回実行時に handle から自動解決してキャッシュする。
事前にわかっているものは記入しておく。
"""

CHANNELS = [
    # ── Tier 1: ホテル・ポイント系 ──
    {
        "handle": "@NonstopDan",
        "channel_id": "",
        "name": "Nonstop Dan",
        "tier": 1,
        "note": "航空レビュー、ポイント活用。企画フォーマットが参考になる。",
    },
    {
        "handle": "@ProjectUntethered",
        "channel_id": "",
        "name": "Project Untethered",
        "tier": 1,
        "note": "ホテルポイント最適化、マリオット/ヒルトン比較。Shoと最も近い領域。",
    },
    {
        "handle": "@PortableProfessional",
        "channel_id": "",
        "name": "Portable Professional",
        "tier": 1,
        "note": "ホテルレビュー、エリート特典検証。実体験ベース。",
    },
    {
        "handle": "@BenThoennes",
        "channel_id": "",
        "name": "Ben Thoennes Dream Vacations",
        "tier": 1,
        "note": "ハワイ・ディズニー特化。子連れ旅行。Shoの視聴者層と重なる。",
    },
    {
        "handle": "@DeniandMia",
        "channel_id": "",
        "name": "Deni & Mia",
        "tier": 1,
        "note": "ポイント・マイル活用、ホテルレビュー。カップル旅行。",
    },
    {
        "handle": "@PrinceofTravel",
        "channel_id": "",
        "name": "Prince of Travel",
        "tier": 1,
        "note": "ポイント最適化、航空レビュー。カナダ拠点だがグローバル。",
    },
    # ── Tier 2: ラグジュアリー・ホテルレビュー系 ──
    {
        "handle": "@JoshCahill",
        "channel_id": "",
        "name": "Josh Cahill",
        "tier": 2,
        "note": "航空・ホテルレビュー。煽り系サムネが特徴的。",
    },
    {
        "handle": "@JebBrooks",
        "channel_id": "",
        "name": "Jeb Brooks",
        "tier": 2,
        "note": "ファーストクラス・ビジネスクラスレビュー。",
    },
    {
        "handle": "@KaraandNate",
        "channel_id": "",
        "name": "Kara and Nate",
        "tier": 2,
        "note": "大手旅行Vlogger。企画の幅が広い。バズるフォーマットの宝庫。",
    },
    {
        "handle": "@WoltersWorld",
        "channel_id": "",
        "name": "Wolters World",
        "tier": 2,
        "note": "「○○のLoves & Hates」フォーマットの元祖。目的地ガイド。",
    },
    {
        "handle": "@SimplyAviation",
        "channel_id": "",
        "name": "Simply Aviation",
        "tier": 2,
        "note": "丁寧な航空レビュー。品のあるスタイル。",
    },
    {
        "handle": "@PaulLucas",
        "channel_id": "",
        "name": "Paul Lucas",
        "tier": 2,
        "note": "ブリティッシュな航空・ホテルレビュー。",
    },
    # ── Tier 3: ファミリー旅行系 ──
    {
        "handle": "@TheBucketListFamily",
        "channel_id": "",
        "name": "The Bucket List Family",
        "tier": 3,
        "note": "家族旅行の最大手。企画の振り切り方が参考になる。",
    },
    {
        "handle": "@FlyingTheNest",
        "channel_id": "",
        "name": "Flying The Nest",
        "tier": 3,
        "note": "家族旅行Vlog。オーストラリア拠点。",
    },
    {
        "handle": "@TheEndlessAdventure",
        "channel_id": "",
        "name": "The Endless Adventure",
        "tier": 3,
        "note": "カップル→ファミリー旅行に移行中。",
    },
    {
        "handle": "@HeyNadine",
        "channel_id": "",
        "name": "Hey Nadine",
        "tier": 3,
        "note": "ファミリー旅行＋実用Tips。",
    },
    # ── Tier 4: 一般旅行系（バイラル企画発掘用） ──
    {
        "handle": "@DrewBinsky",
        "channel_id": "",
        "name": "Drew Binsky",
        "tier": 4,
        "note": "全カ国制覇。ストーリーテリング型。",
    },
    {
        "handle": "@MarkWiens",
        "channel_id": "",
        "name": "Mark Wiens",
        "tier": 4,
        "note": "フード×旅行。タイ拠点。",
    },
    {
        "handle": "@LostLeBlanc",
        "channel_id": "",
        "name": "Lost LeBlanc",
        "tier": 4,
        "note": "シネマティック旅行Vlog。映像クオリティの参考に。",
    },
    {
        "handle": "@YesTheory",
        "channel_id": "",
        "name": "Yes Theory",
        "tier": 4,
        "note": "チャレンジ系旅行。企画力が異常に高い。",
    },
    # ── Tier 5: ハワイ・リゾート特化 ──
    {
        "handle": "@HawaiiActivities",
        "channel_id": "",
        "name": "Hawaii Activities",
        "tier": 5,
        "note": "ハワイのアクティビティ・グルメ情報。",
    },
    {
        "handle": "@LivinginHawaii",
        "channel_id": "",
        "name": "Living in Hawaii",
        "tier": 5,
        "note": "ハワイのローカル情報。",
    },
    {
        "handle": "@BeatofHawaii",
        "channel_id": "",
        "name": "Beat of Hawaii",
        "tier": 5,
        "note": "ハワイの航空・旅行ニュース。",
    },
    # ── Tier 6: 旅行ハック・コスト検証系 ──
    {
        "handle": "@TravelingwithKristin",
        "channel_id": "",
        "name": "Traveling with Kristin",
        "tier": 6,
        "note": "コスト公開系旅行。透明性が高い。",
    },
    {
        "handle": "@SorelleAmore",
        "channel_id": "",
        "name": "Sorelle Amore",
        "tier": 6,
        "note": "旅行ライフスタイル。企画の多様性。",
    },
    {
        "handle": "@LexieLimitless",
        "channel_id": "",
        "name": "Lexie Limitless",
        "tier": 6,
        "note": "若手旅行YouTuber。トレンドに敏感。",
    },
    {
        "handle": "@IndigoTraveller",
        "channel_id": "",
        "name": "Indigo Traveller",
        "tier": 6,
        "note": "ドキュメンタリー型旅行。深い取材。",
    },
    {
        "handle": "@GabrielTraveler",
        "channel_id": "",
        "name": "Gabriel Traveler",
        "tier": 6,
        "note": "バジェット旅行。コスト意識が高い。",
    },
    {
        "handle": "@MikeCorey",
        "channel_id": "",
        "name": "Mike Corey",
        "tier": 6,
        "note": "極端な体験系旅行。企画力。",
    },
    {
        "handle": "@SuitcaseMonkey",
        "channel_id": "",
        "name": "Suitcase Monkey",
        "tier": 6,
        "note": "ミニマリスト旅行。シティガイド。",
    },
]

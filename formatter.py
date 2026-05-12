from datetime import datetime


def format_brief(articles: list[dict]) -> str:
    today = datetime.now().strftime("%A, %B %d %Y")
    lines = [
        f"✈️ *Aviation Morning Brief*",
        f"📅 {today}",
        f"{'─' * 30}",
        "",
    ]

    if not articles:
        lines.append("No major aviation news found in the last 24 hours.")
        return "\n".join(lines)

    for i, art in enumerate(articles, start=1):
        lines.append(f"*{i}. {art['title']}*")
        lines.append(f"🗞 _{art['source']}_")
        if art.get("summary"):
            lines.append(art["summary"])
        if art.get("link"):
            lines.append(f"🔗 {art['link']}")
        lines.append("")

    lines.append("─" * 30)
    lines.append("_Powered by Aviation Brief Bot_ 🛫")

    return "\n".join(lines)

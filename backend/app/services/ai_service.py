from __future__ import annotations

from collections import Counter
import re


def _clean_text(text: str) -> str:
    compact = re.sub(r"\s+", " ", text or "").strip()
    return compact


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[。！？.!?])\s+", text)
    return [p.strip() for p in parts if p.strip()]


def _keywords(text: str, limit: int = 4) -> list[str]:
    tokens = re.findall(r"[A-Za-z]{4,}|[\u4e00-\u9fff]{2,}", text)
    stop_words = {
        "this",
        "that",
        "with",
        "from",
        "were",
        "have",
        "研究",
        "结果",
        "方法",
        "通过",
        "以及",
        "进行",
    }
    filtered = [t.lower() for t in tokens if t.lower() not in stop_words]
    counter = Counter(filtered)
    return [word for word, _ in counter.most_common(limit)]


def _pseudo_translate_zh_to_en(text: str) -> str:
    if not text:
        return ""
    return f"[EN] {text}"


def _pseudo_translate_en_to_zh(text: str) -> str:
    if not text:
        return ""
    return f"[中文] {text}"


def build_ai_analysis(source_text: str, title: str) -> dict:
    text = _clean_text(source_text)
    sents = _sentences(text)

    concise_summary = " ".join(sents[:2]) if sents else "文档未提取到可用正文。"
    core_points = sents[2:5] if len(sents) > 2 else ["核心观点提取中，可补充更多正文后重试。"]

    keywords = _keywords(text)
    method = (
        f"基于关键词 {', '.join(keywords)} 的启发式抽取，结合首段与高频句式进行结构化归纳。"
        if keywords
        else "基于启发式规则完成首版结构化分析。"
    )

    conclusion = sents[-1] if sents else "暂无结论信息。"

    summary_en = _pseudo_translate_zh_to_en(concise_summary)
    summary_zh = _pseudo_translate_en_to_zh(concise_summary)

    mindmap_markdown = "\n".join(
        [
            "```mermaid",
            "mindmap",
            "  root((文献分析))",
            f"    标题::{title}",
            f"    精简摘要::{concise_summary[:80] or '无'}",
            f"    研究方法::{method[:80]}",
            f"    核心观点::{'; '.join(core_points)[:100]}",
            f"    结论::{conclusion[:80]}",
            "```",
        ]
    )

    return {
        "concise_summary": concise_summary,
        "core_points": core_points,
        "research_method": method,
        "conclusion": conclusion,
        "translations": {
            "summary_zh": summary_zh,
            "summary_en": summary_en,
        },
        "mindmap_markdown": mindmap_markdown,
    }

from __future__ import annotations

from collections import Counter
import json
import re
from typing import Any
from urllib import error, request

from app.core.config import settings


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _sentences(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"(?<=[。！？.!?])\s+", text) if p.strip()]


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
    return [w for w, _ in Counter(filtered).most_common(limit)]


def _heuristic_analysis(source_text: str, title: str) -> dict[str, Any]:
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
            "summary_zh": f"[中文] {concise_summary}",
            "summary_en": f"[EN] {concise_summary}",
        },
        "mindmap_markdown": mindmap_markdown,
        "engine": "heuristic",
    }


def _llm_analysis(source_text: str, title: str) -> dict[str, Any] | None:
    if not settings.ai_base_url or not settings.ai_model or not settings.ai_api_key:
        return None

    prompt = (
        "你是学术文献分析助手。请基于输入正文返回 JSON，字段必须完整："
        "concise_summary(string), core_points(array of strings), research_method(string), "
        "conclusion(string), translations(object with summary_zh and summary_en), "
        "mindmap_markdown(string, 使用mermaid mindmap代码块)."
    )

    payload = {
        "model": settings.ai_model,
        "messages": [
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": f"标题: {title}\n正文:\n{source_text[:6000]}",
            },
        ],
        "temperature": 0.2,
    }

    req = request.Request(
        url=f"{settings.ai_base_url.rstrip('/')}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.ai_api_key}",
        },
    )

    try:
        with request.urlopen(req, timeout=20) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        content = body["choices"][0]["message"]["content"]
        # 允许模型返回 ```json 包裹
        content = content.strip()
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?", "", content).strip()
            content = re.sub(r"```$", "", content).strip()
        data = json.loads(content)
        data["engine"] = "llm"
        return data
    except (error.URLError, error.HTTPError, TimeoutError, KeyError, ValueError, json.JSONDecodeError):
        return None


def build_ai_analysis(source_text: str, title: str) -> dict[str, Any]:
    if settings.ai_provider.lower() in {"openai", "openai-compatible", "llm"}:
        llm_result = _llm_analysis(source_text=source_text, title=title)
        if llm_result:
            return llm_result
    return _heuristic_analysis(source_text=source_text, title=title)

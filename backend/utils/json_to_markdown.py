"""
JSON 到 Markdown 转换工具
用于将 Agent 输出的 JSON 格式报告转换为美观的 Markdown 格式
支持 Fusion Agent、News Agent、SEC Agent、Fundamentals Agent、Technical Agent 等
"""

import json
from typing import Dict, Any, Optional


def json_to_markdown(content: str) -> str:
    """
    主转换函数：自动检测内容类型并转换

    Args:
        content: 可能是 JSON 字符串或原始 Markdown 的内容

    Returns:
        Markdown 格式的字符串
    """
    # 如果内容为空，直接返回
    if not content or not content.strip():
        return content

    # 尝试解析 JSON
    try:
        # 移除可能的代码块标记
        parse_content = content
        if parse_content.startswith('```json') and parse_content.endswith('```'):
            parse_content = parse_content[len('```json'):-len('```')].strip()

        data = json.loads(parse_content)

        # 检测报告类型并转换
        if isinstance(data, dict) and 'fusion_summary' in data:
            return fusion_report_to_markdown(data)
        elif isinstance(data, dict) and 'key_news_summary' in data:
            return news_report_to_markdown(data)
        elif isinstance(data, dict) and 'key_filing_changes' in data:
            return sec_report_to_markdown(data)
        elif isinstance(data, dict) and 'valuation_analysis' in data:
            return fundamentals_report_to_markdown(data)
        elif isinstance(data, dict) and 'trend_analysis' in data:
            return technical_report_to_markdown(data)
        elif isinstance(data, dict) and 'installed_skills' in data:
            return custom_skill_report_to_markdown(data)

        # 未识别的格式，返回原始内容
        return content

    except Exception:
        # 任何错误都直接返回原始内容
        return content


def fusion_report_to_markdown(data: Dict[str, Any]) -> str:
    """
    转换 Fusion Agent 报告

    支持格式：
    {
        "fusion_summary": "...",
        "agent_weights": {...},
        "consensus_analysis": {...},
        "risk_assessment": {...},
        "actionable_recommendations": {...},
        "investment_style_alignment": {...},
        "ticker_specific_notes": "...",
        "disclaimer": "..."
    }
    """
    md_parts = []

    # 融合总结
    if isinstance(data, dict) and 'fusion_summary' in data:
        md_parts.append("## 📝 融合分析总结")
        md_parts.append(str(data['fusion_summary']))
        md_parts.append("")

    # Agent 权重
    if isinstance(data, dict) and 'agent_weights' in data:
        md_parts.append("## ⚖️ Agent 权重分配")
        agent_weights = data['agent_weights']

        if isinstance(agent_weights, dict):
            # 表格格式
            md_parts.append("| Agent | 权重 | 置信度 |")
            md_parts.append("|-------|------|--------|")

            for agent, info in agent_weights.items():
                if isinstance(info, dict):
                    weight = info.get('weight', 'N/A')
                    confidence = info.get('confidence', 'N/A')
                    md_parts.append(f"| {agent} | {weight} | {confidence} |")
                else:
                    md_parts.append(f"| {agent} | {info} | N/A |")

            md_parts.append("")

    # 共识分析
    if isinstance(data, dict) and 'consensus_analysis' in data:
        consensus = data['consensus_analysis']
        if isinstance(consensus, dict):
            md_parts.append("## 🤝 共识分析")

            if 'strong_consensus' in consensus and consensus['strong_consensus']:
                md_parts.append("### 强共识点")
                items = consensus['strong_consensus']
                if isinstance(items, list):
                    for point in items:
                        md_parts.append(f"- {point}")

            if 'moderate_consensus' in consensus and consensus['moderate_consensus']:
                md_parts.append("### 中等共识点")
                items = consensus['moderate_consensus']
                if isinstance(items, list):
                    for point in items:
                        md_parts.append(f"- {point}")

            if 'divergence_points' in consensus and consensus['divergence_points']:
                md_parts.append("### 分歧点")
                items = consensus['divergence_points']
                if isinstance(items, list):
                    for point in items:
                        if isinstance(point, dict):
                            title = point.get('issue', '未命名分歧')
                            md_parts.append(f"#### {title}")
                            involved = point.get('agents_involved', 'N/A')
                            reason = point.get('reason', 'N/A')
                            impact = point.get('impact', 'N/A')
                            md_parts.append(f"- **涉及Agent**: {involved}")
                            md_parts.append(f"- **原因**: {reason}")
                            md_parts.append(f"- **影响**: {impact}")
                        else:
                            md_parts.append(f"- {point}")

            md_parts.append("")

    # 风险评估
    if isinstance(data, dict) and 'risk_assessment' in data:
        risk = data['risk_assessment']
        if isinstance(risk, dict):
            md_parts.append("## ⚠️ 风险评估")

            if 'overall_risk_level' in risk:
                md_parts.append(f"**整体风险等级**: {risk['overall_risk_level']}")

            if 'key_risks' in risk and risk['key_risks']:
                md_parts.append("### 关键风险点")
                items = risk['key_risks']
                if isinstance(items, list):
                    for risk_point in items:
                        md_parts.append(f"- {risk_point}")

            if 'risk_categories' in risk and risk['risk_categories']:
                md_parts.append("### 风险分类")
                categories = risk['risk_categories']
                if isinstance(categories, dict):
                    for category, description in categories.items():
                        md_parts.append(f"- **{category}**: {description}")
                elif isinstance(categories, list):
                    for category in categories:
                        md_parts.append(f"- {category}")

            if 'risk_mitigation' in risk and risk['risk_mitigation']:
                md_parts.append("### 风险缓解建议")
                items = risk['risk_mitigation']
                if isinstance(items, list):
                    for suggestion in items:
                        md_parts.append(f"- {suggestion}")

            md_parts.append("")

    # 可行动建议
    if isinstance(data, dict) and 'actionable_recommendations' in data:
        recommendations = data['actionable_recommendations']
        if isinstance(recommendations, dict):
            md_parts.append("## 🎯 可行动建议")

            if 'recommendation_type' in recommendations:
                md_parts.append(f"**建议类型**: {recommendations['recommendation_type']}")

            if 'confidence_level' in recommendations:
                md_parts.append(f"**置信度**: {recommendations['confidence_level']}%")

            if 'time_horizon' in recommendations:
                md_parts.append(f"**适用时间框架**: {recommendations['time_horizon']}")

            if 'specific_actions' in recommendations:
                actions = recommendations['specific_actions']
                if isinstance(actions, dict):
                    md_parts.append("### 具体行动")

                    if 'entry_strategy' in actions:
                        md_parts.append(f"- **入场策略**: {actions['entry_strategy']}")

                    if 'position_size' in actions:
                        md_parts.append(f"- **仓位建议**: {actions['position_size']}")

                    if 'stop_loss' in actions:
                        md_parts.append(f"- **止损位**: {actions['stop_loss']}")

                    if 'take_profit' in actions:
                        md_parts.append(f"- **止盈位**: {actions['take_profit']}")

            if 'decision_factors' in recommendations and recommendations['decision_factors']:
                md_parts.append("### 决策因素")
                items = recommendations['decision_factors']
                if isinstance(items, list):
                    for factor in items:
                        md_parts.append(f"- {factor}")

            md_parts.append("")

    # 投资风格匹配度
    if isinstance(data, dict) and 'investment_style_alignment' in data:
        alignment = data['investment_style_alignment']
        if isinstance(alignment, dict):
            md_parts.append("## 🎨 投资风格匹配度")

            if 'alignment_score' in alignment:
                md_parts.append(f"**匹配度评分**: {alignment['alignment_score']}/100")

            if 'alignment_analysis' in alignment:
                md_parts.append(alignment['alignment_analysis'])

            md_parts.append("")

    # 免责声明
    if isinstance(data, dict) and 'disclaimer' in data:
        md_parts.append("## ⚖️ 免责声明")
        md_parts.append(str(data['disclaimer']))

    return '\n'.join(md_parts)


def news_report_to_markdown(data: Dict[str, Any]) -> str:
    """
    转换 News Agent 报告
    """
    md_parts = []
    md_parts.append("## 📰 新闻分析报告")

    if isinstance(data, dict) and 'key_news_summary' in data and data['key_news_summary']:
        md_parts.append("### 🎯 关键新闻摘要")
        items = data['key_news_summary']
        if isinstance(items, list):
            for news in items:
                md_parts.append(f"- {news}")
        md_parts.append("")

    if isinstance(data, dict) and 'market_sentiment' in data and isinstance(data['market_sentiment'], dict):
        sentiment = data['market_sentiment']
        md_parts.append("### 📊 市场情绪分析")
        if 'overall_sentiment' in sentiment:
            md_parts.append(f"**整体情绪**: {sentiment['overall_sentiment']}")
        if 'sentiment_score' in sentiment:
            md_parts.append(f"**情绪评分**: {sentiment['sentiment_score']}/100")
        if 'sentiment_trend' in sentiment:
            md_parts.append(f"**情绪趋势**: {sentiment['sentiment_trend']}")
        md_parts.append("")

    return '\n'.join(md_parts)


def sec_report_to_markdown(data: Dict[str, Any]) -> str:
    """
    转换 SEC Agent 报告
    """
    md_parts = []
    md_parts.append("## 📋 SEC 文件分析报告")

    if isinstance(data, dict) and 'key_filing_changes' in data and data['key_filing_changes']:
        md_parts.append("### 📊 关键文件变化")
        md_parts.append(str(data['key_filing_changes']))
        md_parts.append("")

    return '\n'.join(md_parts)


def fundamentals_report_to_markdown(data: Dict[str, Any]) -> str:
    """
    转换 Fundamentals Agent 报告
    """
    md_parts = []
    md_parts.append("## 📊 基本面分析报告")

    if isinstance(data, dict) and 'overall_score' in data:
        md_parts.append(f"## 🎯 综合评分: {data['overall_score']}/100")

    if isinstance(data, dict) and 'investment_thesis' in data and data['investment_thesis']:
        md_parts.append("## 💡 投资论点")
        items = data['investment_thesis']
        if isinstance(items, list):
            for thesis in items:
                md_parts.append(f"- {thesis}")

    if isinstance(data, dict) and 'key_concerns' in data and data['key_concerns']:
        md_parts.append("## ⚠️ 关键关注点")
        items = data['key_concerns']
        if isinstance(items, list):
            for concern in items:
                md_parts.append(f"- {concern}")

    return '\n'.join(md_parts)


def technical_report_to_markdown(data: Dict[str, Any]) -> str:
    """
    转换 Technical Agent 报告
    """
    md_parts = []
    md_parts.append("## 📈 技术分析报告")

    if isinstance(data, dict) and 'technical_score' in data:
        md_parts.append(f"## 📊 技术评分: {data['technical_score']}/100")

    return '\n'.join(md_parts)


def custom_skill_report_to_markdown(data: Dict[str, Any]) -> str:
    """
    转换 Custom Skill Agent 报告
    """
    md_parts = []
    md_parts.append("## 🔧 自定义技能分析")

    if isinstance(data, dict) and 'installed_skills' in data and data['installed_skills']:
        md_parts.append("### 已安装技能")
        items = data['installed_skills']
        if isinstance(items, list):
            for skill in items:
                md_parts.append(f"- {skill}")
        md_parts.append("")

    return '\n'.join(md_parts)


if __name__ == "__main__":
    # 测试数据
    test_data = {
        "fusion_summary": "综合分析显示，AAPL当前具有强劲的基本面支撑，但短期技术面存在调整压力。",
        "agent_weights": {
            "news_agent": {"weight": "20%", "confidence": 75},
            "sec_agent": {"weight": "20%", "confidence": 55},
            "fundamentals_agent": {"weight": "20%", "confidence": 85},
            "technical_agent": {"weight": "20%", "confidence": 70},
            "custom_skill_agent": {"weight": "20%", "confidence": 82}
        },
        "consensus_analysis": {
            "strong_consensus": [
                "高波动性特征显著，需严格控制单一标的仓位",
                "资产负债表极度健康，现金流造血能力强"
            ],
            "moderate_consensus": [
                "短期面临交付增速放缓与行业价格战压力"
            ],
            "divergence_points": [
                {
                    "issue": "短期盈利压力 vs 长期护城河",
                    "agents_involved": ["News Agent", "Fundamentals Agent"],
                    "reason": "信息来源差异",
                    "impact": "导致对当前买入时机的判断出现分歧"
                }
            ]
        },
        "risk_assessment": {
            "overall_risk_level": "中高",
            "key_risks": [
                "Q1交付下滑与储能放缓若持续，将直接侵蚀自由现金流与毛利率"
            ]
        },
        "actionable_recommendations": {
            "recommendation_type": "持有",
            "confidence_level": 70,
            "time_horizon": "中期"
        }
    }

    # 测试转换
    print("=== Fusion Report Markdown ===")
    print("-" * 50)
    print(fusion_report_to_markdown(test_data))
    print("\n" + "=" * 50 + "\n")

    print("=== 通用转换函数测试 ===")
    print("-" * 50)
    json_str = json.dumps(test_data)
    print(json_to_markdown(json_str))

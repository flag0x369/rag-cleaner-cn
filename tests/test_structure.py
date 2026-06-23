from rag_cleaner_cn.core.pipeline import CleaningPipeline


def test_long_article_promotes_original_standalone_subheadings_to_h2(tmp_path):
    source = tmp_path / "article.md"
    source.write_text(
        """# 长期被打压的人，反应慢是一定的

从前我深以为然，觉得脑子灵光、专注力足，反应就该利落。

把“创伤性卡顿”归为“能力缺陷”

是对受害者最隐蔽的二次伤害。多数人对慢反应的认知，始终困在偏见里。

心理内耗织就的认知闭环

这份卡顿绝非偶然，是长期创伤的惯性。注意力偏移、决策恐惧和表达抑制，会共同拖慢反应。

打破卡顿的关键

打破卡顿的关键，是重建心理安全感。不逼自己快，允许慢下来接纳创伤痕迹。
""",
        encoding="utf-8",
    )

    result = CleaningPipeline.default().run_file(source, tmp_path / "output")
    clean = (tmp_path / "output" / result.document.doc_id / "clean.md").read_text(encoding="utf-8")

    assert "## 把“创伤性卡顿”归为“能力缺陷”" in clean
    assert "## 心理内耗织就的认知闭环" in clean
    assert "## 打破卡顿的关键" in clean
    assert clean.count("# 长期被打压的人，反应慢是一定的") == 1


def test_original_subheading_can_be_followed_by_short_bridge_sentence(tmp_path):
    source = tmp_path / "sales.md"
    source.write_text(
        """# 好心给客户送礼却死活不收，销售该怎么办？

客户的心理账本

首先，客户拒绝收礼的核心原因是：

衡量不清楚投入产出比。他们需要判断礼物背后的期待，以及自己需要为此承担怎样的责任。
""",
        encoding="utf-8",
    )

    result = CleaningPipeline.default().run_file(source, tmp_path / "output")
    clean = (tmp_path / "output" / result.document.doc_id / "clean.md").read_text(encoding="utf-8")

    assert "## 客户的心理账本" in clean


def test_long_article_without_subheadings_gets_generic_structure_anchors(tmp_path):
    source = tmp_path / "plain.md"
    paragraphs = [
        "真正重要的是先把注意力放回长期行动。很多人不是没有机会，而是不断被短期刺激牵着走。"
        "当信息不断涌入，人会误以为自己正在成长，其实只是不断切换注意力。",
        "第一层问题是目标太散。今天看见别人做内容，明天看见别人做社群，后天又想去做投资。"
        "所有选择都看起来有道理，但没有一条线被持续投入。",
        "第二层问题是没有复盘。每次失败以后，只换方向，不分析原因，于是同样的坑会不断重来。"
        "真正有效的复盘，是把动作、反馈、判断和下一步改法写清楚。",
        "第三层问题是缺少稳定输入。没有持续读书、观察和记录，就很难形成自己的判断标准。"
        "判断标准不稳定，行动就会被情绪和外部评价反复带偏。",
        "当一个人愿意把动作收窄，把反馈记下来，把时间投入到同一条主线上，复利才会出现。"
        "复利不是速度，而是稳定方向上的重复投入。",
        "所谓成长，不是每天都很激动，而是每天都能留下一个可以复用的动作或判断。"
        "可复用的东西越多，下一次行动的成本就越低。",
        "这也是为什么慢一点不一定是坏事。慢，意味着你有机会看清楚自己真正依赖的能力。"
        "只要方向没有错，慢反而能减少很多无意义损耗。",
        "如果只能选择一个改变，那就是减少噪声输入，把每天最重要的事提前做完。"
        "先完成关键动作，再去处理其他信息，人的秩序感会立刻恢复。",
        "长期看，稳定行动比短期爆发更可靠。你能坚持什么，最终就会成为什么。"
        "这不是口号，而是绝大多数普通人能够真正复制的成长方式。",
    ]
    source.write_text("# 长期行动\n\n" + "\n\n".join(paragraphs * 3), encoding="utf-8")

    result = CleaningPipeline.default().run_file(source, tmp_path / "output")
    clean = (tmp_path / "output" / result.document.doc_id / "clean.md").read_text(encoding="utf-8")

    assert "## 核心观点" in clean
    assert "## 关键论述" in clean
    assert "## 结尾" in clean
    assert "真正重要的是先把注意力放回长期行动" in clean
    assert any("核心观点" in chunk.section_path for chunk in result.chunks)


def test_short_claim_is_not_forced_into_generic_sections(tmp_path):
    source = tmp_path / "short.md"
    source.write_text("# 短观点\n\n增长不是更多流量，而是更高质量的转化闭环。", encoding="utf-8")

    result = CleaningPipeline.default().run_file(source, tmp_path / "output")
    clean = (tmp_path / "output" / result.document.doc_id / "clean.md").read_text(encoding="utf-8")

    assert "## 核心观点" not in clean
    assert "## 关键论述" not in clean
    assert result.chunks[0].section_path == ["短观点"]

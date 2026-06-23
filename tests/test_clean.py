from rag_cleaner_cn.core.enums import ChunkStatus, NoiseType, RiskTag
from rag_cleaner_cn.core.pipeline import CleaningPipeline


def run_text(text: str):
    return CleaningPipeline.default().run_text(text, metadata={"title": "测试文档"})


def test_wechat_noise_is_dropped_and_claim_is_kept():
    result = run_text(
        """# 增长的本质

增长不是更多流量，而是更高质量的转化闭环。

扫码添加微信，回复 666 领取资料包。

点赞、在看、转发给朋友。"""
    )

    clean_text = "\n".join(segment.text_cleaned or "" for segment in result.segments)

    assert "增长不是更多流量" in clean_text
    assert "扫码添加微信" not in clean_text
    assert "点赞、在看" not in clean_text
    assert [segment.noise_type for segment in result.dropped] == [
        NoiseType.MARKETING,
        NoiseType.MARKETING,
    ]


def test_marketing_keywords_inside_analysis_are_not_dropped():
    result = run_text(
        "这个训练营的价格从 199 提到 999，不是简单涨价，而是交付深度和用户筛选机制发生了变化。"
    )

    assert result.manifest.kept_segments == 1
    assert result.chunks[0].chunk_status in {ChunkStatus.IMPORT_CHUNK, ChunkStatus.IMPORT_SHORT}
    assert "训练营的价格" in result.chunks[0].text


def test_wechat_keyword_inside_private_domain_method_is_not_dropped():
    result = run_text("添加企业微信是私域承接链路的关键动作。")

    assert result.manifest.kept_segments == 1
    assert result.manifest.dropped_segments == 0
    assert "添加企业微信" in result.chunks[0].embedding_text_main


def test_pure_follow_account_prompt_is_dropped():
    result = run_text(
        """点击下方👇“进化思维”关注公众号

真正重要的是把注意力放回自己的长期行动。"""
    )

    assert result.manifest.dropped_segments == 1
    assert "关注公众号" not in result.chunks[0].embedding_text_main
    assert "长期行动" in result.chunks[0].embedding_text_main


def test_pure_account_growth_and_freebie_prompts_are_dropped():
    result = run_text(
        """👆关注进化思维成长不迷路

🌹点击👇领取免费读物

20000+政企销售在这里沉淀人脉、联合拓客、寻找产品

真正重要的是把注意力放回客户问题本身。"""
    )

    clean_text = "\n".join(segment.text_cleaned or "" for segment in result.segments)
    assert result.manifest.dropped_segments == 3
    assert "成长不迷路" not in clean_text
    assert "免费读物" not in clean_text
    assert "联合拓客" not in clean_text
    assert "客户问题本身" in result.chunks[0].embedding_text_main


def test_wechat_footer_subscription_friend_circle_and_author_prompts_are_dropped():
    result = run_text(
        """全 文 完

## 欢迎点击下方卡片 持续订阅我的内容

我读了几百本书，筛选了优质的20本书单，放在我的朋友圈置顶了，欢迎添加我👇微信领取书单

## 欢迎加入我的朋友圈

长期分享感悟、书单、思维等等欢迎加入我的朋友圈长期分享感悟、书单、思维等等

购买链接：

## 赚钱思维 | 财富故事 | 深谙人性 | 认知提升

👇点个关注，下一篇更精彩。

⭐关于作者：欢迎关注👇我的个人成长公众号

真正重要的是把注意力放回正文观点本身。"""
    )

    clean_text = "\n".join(segment.text_cleaned or "" for segment in result.segments)
    assert result.manifest.dropped_segments == 9
    assert "全 文 完" not in clean_text
    assert "持续订阅我的内容" not in clean_text
    assert "微信领取书单" not in clean_text
    assert "欢迎加入我的朋友圈" not in clean_text
    assert "购买链接" not in clean_text
    assert "个人成长公众号" not in clean_text
    assert "正文观点本身" in result.chunks[0].embedding_text_main


def test_footer_keywords_inside_meaningful_analysis_are_not_dropped():
    result = run_text("朋友圈和书单都可以作为私域触点，但购买链接必须服务于用户真实需求。")

    assert result.manifest.dropped_segments == 0
    assert "朋友圈和书单" in result.chunks[0].embedding_text_main


def test_guangzhi_trailing_promotion_block_is_dropped():
    result = run_text(
        """真正决定项目成败的大事，是建立高层客户的关系。

1、链接广智

2、广智的大客户销售指南电子版购买链接

71万字、1200页、全网销量10000+、100%好评、7天可退

点击图片了解↓

3、大客户销售训练营介绍（总第22期）

6、更多干货

## 大客户经理必备万字工具文：大客户销售策略汇总

【思考】招投标为什么会被内定？"""
    )

    text = result.chunks[0].embedding_text_main
    assert result.manifest.dropped_segments == 8
    assert "真正决定项目成败" in text
    assert "链接广智" not in text
    assert "购买链接" not in text
    assert "更多干货" not in text
    assert "招投标为什么会被内定" not in text


def test_guangzhi_link_phrase_inside_body_is_not_trailing_block():
    result = run_text("链接广智这个动作，在正文案例里指的是销售如何连接关键人。")

    assert result.manifest.dropped_segments == 0
    assert "链接广智这个动作" in result.chunks[0].embedding_text_main


def test_inline_guangzhi_trailing_promotion_is_trimmed_and_logged():
    result = run_text(
        "真正重要的是前面的客户关系方法。祝你销售顺利。 "
        "1、链接广智 欢迎添加微信，无助理，为本人 "
        "2、广智的新手快速提升课+大客户销售指南电子版购买链接 "
        "70万字、1200页、全网销量10000+、100%好评、7天可退 "
        "点击图片了解↓ 6、更多干货 大客户经理必备万字工具文：大客户销售策略汇总"
    )

    text = result.chunks[0].embedding_text_main
    assert result.manifest.dropped_segments == 1
    assert result.dropped[0].drop_reason == "尾部推广区块"
    assert "前面的客户关系方法" in text
    assert "祝你销售顺利" in text
    assert "链接广智" not in text
    assert "购买链接" not in text
    assert "更多干货" not in text


def test_guangzhi_link_block_and_knowledge_planet_footer_are_dropped():
    result = run_text(
        """真正重要的是前面的客户关系方法。

## PART3、其他

销售训练营课程还在开放预约，倒计时6天，都知道我脾气，买课送我这个人，有问题随时咨询。

学员的反馈都在朋友圈，可以先看看。

另外昨天发布了试听课，大家可以翻一下公众号记录

算了不用翻了，链接↓

## 大客户销售第一课：回归本质找问题

报不报都听一下，省得咱们相逢一场没啥收获，我心里有愧🥺

## PART4、链接

这是我的个人微信

这个公众号以及上述课程是我的副业尝试，欢迎链接。

## 最近注册了一个知识星球

私我我拉你进来。

这是这个公众号值得一读的文章

大客户经理必备万字工具文：大客户销售策略汇总"""
    )

    text = result.chunks[0].embedding_text_main
    assert result.manifest.dropped_segments >= 8
    assert "前面的客户关系方法" in text
    assert "销售训练营课程还在开放预约" not in text
    assert "PART4" not in text
    assert "个人微信" not in text
    assert "知识星球" not in text
    assert "公众号值得一读" not in text


def test_author_bio_and_cooperation_footer_block_is_dropped():
    result = run_text(
        """真正重要的是把注意力放回正文观点本身。

（正文完）

...................................

Tips:

我是差劲先生，曾经创业负债百万，靠公众号五年时间，从负债做到公众号粉丝体量5000万粉丝。想了解公众号的欢迎🔗我。

⭐关于作者经历点击👇查看：

大家好，我是差劲先生

公众号复利合作点击👇查看：

没有复利思维，你赚不到大钱！

🔗公众号复利合作联系微信：328888"""
    )

    text = result.chunks[0].embedding_text_main
    assert result.manifest.dropped_segments == 9
    assert "正文观点本身" in text
    assert "正文完" not in text
    assert "差劲先生" not in text
    assert "作者经历" not in text
    assert "公众号复利合作" not in text
    assert "联系微信" not in text


def test_author_link_footer_without_end_marker_is_dropped():
    result = run_text(
        """想被提拔，先做好价值闭环。

原创文章，不得转载

⭐关于作者经历点击👇查看：

大家好，我是差劲先生

公众号复利合作点击👇查看：

没有复利思维，你赚不到大钱！

手慢无！200 本上班 / 成长 / 交往读物，免费领走不谢（职场 / 体制内必看！）

🔗公众号复利合作联系微信：328888"""
    )

    text = result.chunks[0].embedding_text_main
    assert result.manifest.dropped_segments == 7
    assert "价值闭环" in text
    assert "原创文章，不得转载" not in text
    assert "作者经历" not in text
    assert "差劲先生" not in text
    assert "免费领走" not in text
    assert "联系微信" not in text


def test_tail_follow_personal_wechat_and_long_share_prompts_are_dropped():
    result = run_text(
        """真正重要的是把注意力放回正文观点本身。

点击下方👇“进化思维”关注我，一起从旧模式里出走。

关注我👇愿你每天都能突破一点昨天的自己。

这是我的个人微信，欢迎链接。

放在这就是欢迎你来添加，不用担心不礼貌，太可怕之类的哈~

- END -

长期分享感悟、书单、思维等等"""
    )

    text = result.chunks[0].embedding_text_main
    assert result.manifest.dropped_segments == 6
    assert "正文观点本身" in text
    assert "关注我" not in text
    assert "个人微信" not in text
    assert "欢迎你来添加" not in text
    assert "长期分享感悟" not in text


def test_follow_me_prefix_inside_body_word_is_not_dropped():
    result = run_text("关注我方产品的客户变化，是判断渠道质量的重要信号。")

    assert result.manifest.dropped_segments == 0
    assert "关注我方产品" in result.chunks[0].embedding_text_main


def test_course_launch_prompt_is_dropped_without_dropping_training_analysis():
    result = run_text(
        """新一期大客户销售训练营，已经发车了~

训练营里的复盘方法可以作为正文案例，但不能替代客户现场验证。"""
    )

    text = result.chunks[0].embedding_text_main
    assert result.manifest.dropped_segments == 1
    assert "已经发车" not in text
    assert "训练营里的复盘方法" in text


def test_short_useful_claim_is_imported_as_short_chunk():
    result = run_text("增长不是更多流量，而是更高质量的转化闭环。")

    assert result.manifest.kept_segments == 1
    assert result.chunks[0].chunk_status == ChunkStatus.IMPORT_SHORT


def test_video_filler_words_are_removed_without_dropping_meaning():
    result = run_text("嗯，我们今天呢，主要讲三个问题。第一个问题是用户是谁。")

    text = result.chunks[0].embedding_text_main
    assert "嗯" not in text
    assert "今天呢" not in text
    assert "主要讲三个问题" in text
    assert "用户是谁" in text


def test_demonstrative_inside_domain_phrase_is_preserved():
    result = run_text("这个模型的核心问题是转化链路太长。")

    assert "这个模型" in result.chunks[0].embedding_text_main


def test_stutter_repetition_is_compressed_and_logged():
    result = run_text("我们我们今天讲一下增长增长的核心问题。")

    text = result.chunks[0].embedding_text_main
    assert "我们我们" not in text
    assert "增长增长" not in text
    assert "我们今天讲一下增长的核心问题" in text
    assert any(record.original != record.fixed for record in result.repairs)


def test_media_dependency_is_marked_for_review():
    result = run_text("大家看这里，这个图左边就是我们要关注的重点。")

    assert RiskTag.MEDIA_DEPENDENCY in result.segments[0].risk_tags
    assert result.reviews
    assert RiskTag.MEDIA_DEPENDENCY in result.reviews[0].risk_tags


def test_ocr_cross_page_sentence_break_is_joined():
    result = run_text("增长的关键不是获得更多用户，而是让用户在一个稳定的场景中持续完成\n转化。")

    assert "持续完成转化" in result.chunks[0].embedding_text_main


def test_classroom_interaction_noise_line_is_dropped_and_logged():
    result = run_text(
        """给我扣个一

复杂问题最终要落到和谁持续建联，以及用什么理由持续建联。"""
    )

    assert result.manifest.dropped_segments == 1
    assert result.dropped[0].noise_type == NoiseType.TRANSCRIPT_ARTIFACT
    assert "给我扣个一" not in result.chunks[0].embedding_text_main
    assert "持续建联" in result.chunks[0].embedding_text_main


def test_filler_phrase_with_oral_particles_is_dropped():
    for text in ["对吧啊", "嗯嗯", "啊然后呢", "好不好"]:
        result = run_text(text)

        assert result.chunks == []
        assert result.manifest.dropped_segments == 1


def test_clear_kougeyi_classroom_noise_is_dropped_without_dropping_body_example():
    result = run_text(
        """清楚扣个一

让客户扣个一不是成交方法，而是课堂互动示例。"""
    )

    assert result.manifest.dropped_segments == 1
    assert "清楚扣个一" not in result.chunks[0].embedding_text_main
    assert "扣个一不是成交方法" in result.chunks[0].embedding_text_main


def test_classroom_word_inside_meaningful_sentence_is_kept():
    result = run_text("让客户扣个一不是成交方法，而是课堂互动示例，销售复盘时要回到客户真实问题。")

    assert result.manifest.dropped_segments == 0
    assert "扣个一不是成交方法" in result.chunks[0].embedding_text_main

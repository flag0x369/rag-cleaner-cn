from rag_cleaner_cn.core.pipeline import CleaningPipeline
from rag_cleaner_cn.repair.filler_words import remove_filler_words
from rag_cleaner_cn.repair.repetition import compress_repetition


def test_compress_repetition_returns_changed_text_and_flag():
    fixed, changed = compress_repetition("我们我们今天讲增长增长。")

    assert changed is True
    assert fixed == "我们今天讲增长。"


def test_compress_repetition_preserves_normal_chinese_reduplication():
    fixed, changed = compress_repetition("他明明知道要慢慢来，也会悄悄打分、默默比较。")

    assert changed is False
    assert fixed == "他明明知道要慢慢来，也会悄悄打分、默默比较。"


def test_compress_repetition_preserves_meaningful_abab_phrases():
    fixed, changed = compress_repetition("会不会、能不能、一遍一遍、传着传着，该谈恋爱谈恋爱。")

    assert changed is False
    assert fixed == "会不会、能不能、一遍一遍、传着传着，该谈恋爱谈恋爱。"


def test_sales_course_asr_terms_are_repaired_and_logged():
    result = CleaningPipeline.default().run_text(
        "今天讲乔哈里创，先囚禁已知，再用 SPN 和 BNT 判断项目，避免痛苦恋。"
    )

    text = result.chunks[0].embedding_text_main
    assert "乔哈里窗" in text
    assert "穷尽已知" in text
    assert "SPIN" in text
    assert "BANT" in text
    assert "痛苦链" in text
    assert len(result.repairs) == 1


def test_default_config_does_not_enable_noop_ocr_character_repair():
    assert CleaningPipeline.default().config.repair.enable_ocr_character_fix is False


def test_filler_only_segment_is_dropped_instead_of_repaired_to_empty():
    result = CleaningPipeline.default().run_text("然后呢")

    assert result.repairs == []
    assert result.chunks == []
    assert result.manifest.dropped_segments == 1


def test_remove_filler_words_preserves_original_punctuation_without_filler():
    fixed, changed = remove_filler_words("于是就躲在“我已经够努力了”的错觉里，", ["然后呢"])

    assert changed is False
    assert fixed == "于是就躲在“我已经够努力了”的错觉里，"


def test_remove_filler_words_preserves_rhetorical_question_transition():
    fixed, changed = remove_filler_words("然后呢？发现自己还在原地。", ["然后呢"])

    assert changed is False
    assert fixed == "然后呢？发现自己还在原地。"


def test_remove_oral_particles_inside_transcript_sentence():
    fixed, changed = remove_filler_words(
        "哈喽大家好啊我是广志啊这节课比较重要呃然后呢带大家看一下好不好。",
        ["呃", "啊", "然后呢", "好不好"],
    )

    assert changed is True
    assert "哈喽大家好" not in fixed
    assert "呃" not in fixed
    assert "啊" not in fixed
    assert "然后呢" not in fixed
    assert "好不好" not in fixed
    assert fixed == "这节课比较重要带大家看一下。"


def test_remove_filler_words_preserves_meaningful_classroom_example():
    fixed, changed = remove_filler_words("让客户扣个一不是成交方法，而是课堂互动示例。", ["扣个一"])

    assert changed is False
    assert fixed == "让客户扣个一不是成交方法，而是课堂互动示例。"


def test_remove_filler_words_does_not_repair_to_empty_text():
    fixed, changed = remove_filler_words("啊", ["啊"])

    assert changed is False
    assert fixed == "啊"

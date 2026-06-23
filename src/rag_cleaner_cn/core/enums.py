from enum import StrEnum


class SourceType(StrEnum):
    WECHAT_ARTICLE = "wechat_article"
    WEB_ARTICLE = "web_article"
    BOOK = "book"
    PDF = "pdf"
    EPUB = "epub"
    COURSE_DOC = "course_doc"
    VIDEO_TRANSCRIPT = "video_transcript"
    AUDIO_TRANSCRIPT = "audio_transcript"
    MARKDOWN = "markdown"
    PLAIN_TEXT = "plain_text"
    UNKNOWN = "unknown"


class ParagraphType(StrEnum):
    TITLE = "title"
    HEADING = "heading"
    BODY_CLAIM = "body_claim"
    DEFINITION = "definition"
    PRINCIPLE = "principle"
    METHOD = "method"
    STEP = "step"
    EXAMPLE = "example"
    CASE = "case"
    QUOTE = "quote"
    QUESTION = "question"
    ANSWER = "answer"
    LIST = "list"
    TABLE_TEXT = "table_text"
    IMAGE_CAPTION = "image_caption"
    TRANSCRIPT_SPEECH = "transcript_speech"
    TRANSCRIPT_QUESTION = "transcript_question"
    TRANSCRIPT_ANSWER = "transcript_answer"
    MARKETING = "marketing"
    FOOTER = "footer"
    COPYRIGHT = "copyright"
    NAVIGATION = "navigation"
    DIRECTORY = "directory"
    NOISE = "noise"
    UNKNOWN = "unknown"


class ContentValue(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class SegmentAction(StrEnum):
    KEEP = "keep"
    NORMALIZE = "normalize"
    REPAIR = "repair"
    REVIEW = "review"
    DROP = "drop"


class NoiseType(StrEnum):
    NONE = "none"
    MARKETING = "marketing"
    FOOTER = "footer"
    COPYRIGHT = "copyright"
    NAVIGATION = "navigation"
    DUPLICATED = "duplicated"
    EMPTY = "empty"
    HTML_RESIDUE = "html_residue"
    TIMESTAMP_ONLY = "timestamp_only"
    IMAGE_PLACEHOLDER = "image_placeholder"
    TRANSCRIPT_ARTIFACT = "transcript_artifact"
    DIRECTORY = "directory"
    PAGE_HEADER = "page_header"
    PAGE_FOOTER = "page_footer"
    URL_ONLY = "url_only"
    DECORATION = "decoration"


class RiskTag(StrEnum):
    POSSIBLE_ASR_ERROR = "possible_asr_error"
    POSSIBLE_OCR_ERROR = "possible_ocr_error"
    SEMANTIC_BREAK = "semantic_break"
    MEDIA_DEPENDENCY = "media_dependency"
    MISSING_CONTEXT = "missing_context"
    SPEAKER_CONFUSION = "speaker_confusion"
    TABLE_LOSS = "table_loss"
    IMAGE_LOSS = "image_loss"
    FORMULA_LOSS = "formula_loss"
    DOMAIN_TERM_UNKNOWN = "domain_term_unknown"
    LOW_CONFIDENCE_REPAIR = "low_confidence_repair"


class QualityTag(StrEnum):
    CLEAN = "clean"
    SHORT_BUT_USEFUL = "short_but_useful"
    PARTIAL_CONTEXT = "partial_context"
    WEAK_STRUCTURE = "weak_structure"
    DUPLICATE_CANDIDATE = "duplicate_candidate"
    MARKETING_REMOVED = "marketing_removed"
    FOOTER_REMOVED = "footer_removed"
    OCR_NOISE = "ocr_noise"
    ASR_NOISE = "asr_noise"
    MEDIA_DEPENDENT = "media_dependent"
    NEEDS_REVIEW = "needs_review"


class RepairType(StrEnum):
    PUNCTUATION_RESTORE = "punctuation_restore"
    SENTENCE_BOUNDARY_RESTORE = "sentence_boundary_restore"
    FILLER_WORD_REMOVAL = "filler_word_removal"
    REPETITION_COMPRESSION = "repetition_compression"
    ASR_HOMOPHONE_FIX = "asr_homophone_fix"
    OCR_CHARACTER_FIX = "ocr_character_fix"
    PROPER_NOUN_FIX = "proper_noun_fix"
    NUMBER_FORMAT_FIX = "number_format_fix"
    LIST_STRUCTURE_FIX = "list_structure_fix"
    HEADING_STRUCTURE_FIX = "heading_structure_fix"
    SPEAKER_TURN_FIX = "speaker_turn_fix"


class Confidence(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DocumentStatus(StrEnum):
    IMPORT_CORE = "import_core"
    IMPORT_CHUNKED = "import_chunked"
    REVIEW = "review"
    EXCLUDE = "exclude"


class ChunkStatus(StrEnum):
    IMPORT_CHUNK = "import_chunk"
    IMPORT_SHORT = "import_short"
    REVIEW_CHUNK = "review_chunk"
    EXCLUDE_CHUNK = "exclude_chunk"


class ChunkType(StrEnum):
    CLAIM = "claim"
    METHOD = "method"
    CASE = "case"
    STEP = "step"
    QA = "qa"
    DEFINITION = "definition"
    QUOTE = "quote"
    TRANSCRIPT = "transcript"
    MIXED = "mixed"

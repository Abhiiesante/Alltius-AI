from dataclasses import dataclass, field
from typing import List, Optional, Literal, Union, Any

BlockType = Literal["paragraph", "table", "chart", "footnote"]

@dataclass
class ContentBlock:
    type: BlockType
    page_number: int
    section: Optional[str] = None
    sub_section: Optional[str] = None
    confidence: Optional[float] = None  # block-level extraction / classification confidence
    metadata: dict = field(default_factory=dict)

@dataclass
class ParagraphBlock(ContentBlock):
    text: str = ""
    bbox: tuple | None = None  # (x0,y0,x1,y1) not serialized

@dataclass
class TableBlock(ContentBlock):
    table_data: List[List[str]] = field(default_factory=list)
    description: Optional[str] = None
    bbox: tuple | None = None  # not serialized

@dataclass
class ChartBlock(ContentBlock):
    description: Optional[str] = None
    extracted_data: Optional[List[List[str]]] = None  # heuristic table extracted from chart if any OCR pass

@dataclass
class FootnoteBlock(ContentBlock):
    text: str = ""

Block = Union[ParagraphBlock, TableBlock, ChartBlock]

@dataclass
class PageResult:
    page_number: int
    content: List[Block] = field(default_factory=list)

@dataclass
class ExtractionResult:
    pages: List[PageResult] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "pages": [
                {
                    "page_number": p.page_number,
                    "content": [self._block_to_dict(b) for b in p.content],
                }
                for p in self.pages
            ]
        }

    def _block_to_dict(self, b: Block) -> dict:
        base = {
            "type": b.type,
            "section": b.section,
            "sub_section": b.sub_section,
        }
        if isinstance(b, ParagraphBlock):
            base["text"] = b.text
        elif isinstance(b, TableBlock):
            base["table_data"] = b.table_data
            base["description"] = b.description
        elif isinstance(b, ChartBlock):
            base["description"] = b.description
            base["extracted_data"] = b.extracted_data
        elif isinstance(b, FootnoteBlock):
            base["text"] = b.text
        # include confidence if present
        if b.confidence is not None:
            base["confidence"] = b.confidence
        if b.metadata:
            base["metadata"] = b.metadata
        return base

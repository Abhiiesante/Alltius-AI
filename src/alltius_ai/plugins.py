from __future__ import annotations
from typing import List, Protocol
from .models import ExtractionResult, ParagraphBlock

class Plugin(Protocol):
    name: str
    def process(self, result: ExtractionResult) -> None: ...

# Registry
_PLUGIN_REGISTRY = {}

def register(plugin: Plugin):
    _PLUGIN_REGISTRY[plugin.name] = plugin

# Example plugin: add word counts to paragraph metadata
class WordCountPlugin:
    name = "wordcount"
    def process(self, result: ExtractionResult) -> None:
        for page in result.pages:
            for block in page.content:
                if isinstance(block, ParagraphBlock):
                    wc = len(block.text.split())
                    block.metadata["word_count"] = wc

# auto-register
register(WordCountPlugin())

def run_plugins(result: ExtractionResult, plugin_names: List[str]):
    for name in plugin_names:
        plugin = _PLUGIN_REGISTRY.get(name)
        if plugin:
            plugin.process(result)

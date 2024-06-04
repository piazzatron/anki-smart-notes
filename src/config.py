from typing import Dict, TypedDict, Literal
from aqt import mw


class NoteTypeMap(TypedDict):
    fields: Dict[str, str]


class PromptMap(TypedDict):
    note_types: Dict[str, NoteTypeMap]


OpenAIModels = Literal["gpt-3.5-turbo", "gpt-4o", "gpt-4-turbo", "gpt-4"]


class Config:
    """Fancy config class that uses the Anki addon manager to store config values."""

    openai_api_key: str
    prompts_map: PromptMap
    openai_model: OpenAIModels

    def __getattr__(self, key: str) -> object:
        if not mw:
            raise Exception("Error: mw not found")

        return mw.addonManager.getConfig(__name__).get(key)  # type: ignore[union-attr]

    def __setattr__(self, name: str, value: object) -> None:
        if not mw:
            raise Exception("Error: mw not found")

        old_config = mw.addonManager.getConfig(__name__)
        if not old_config:
            raise Exception("Error: no config found")

        old_config[name] = value
        mw.addonManager.writeConfig(__name__, old_config)

    def get_prompt(self, note_type: str, field: str):
        return (
            self.prompts_map.get("note_types", {})
            .get(note_type, {"fields": {}})
            .get("fields", {})
            .get(field, None)
        )


config = Config()

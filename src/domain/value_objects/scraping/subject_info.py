from dataclasses import dataclass
import re
from urllib.parse import quote

SUBJECT_ALIAS_MAP = {
    "Математика. Базовый уровень": "math",
    "Математика. Профильный уровень": "promath",
    "Информатика и ИКТ": "inf",
    "Русский язык": "rus",
    "Физика": "phis",
    "Химия": "him",
    "Биология": "bio",
    "История": "hist",
    "Обществознание": "soc",
    "Литература": "lit",
    "География": "geo",
    "Английский язык": "eng",
    "Немецкий язык": "ger",
    "Французский язык": "fra",
    "Испанский язык": "esp",
    "Китайский язык": "chi"
}

SUBJECT_TO_PROJ_ID_MAP = {
    "math": "E040A72A1A3DABA14C90C97E0B6EE7DC",
    "promath": "AC437B34557F88EA4115D2F374B0A07B",
    "inf": "B9ACA5BBB2E19E434CD6BEC25284C67F",
    "rus": "AF0ED3F2557F8FFC4C06F80B6803FD26",
    "phis": "BA1F39653304A5B041B656915DC36B38",
    "him": "5BAC840990A3AF0A4EE80D1B5A1F9527",
    "bio": "CA9D848A31849ED149D382C32A7A2BE4",
    "hist": "068A227D253BA6C04D0C832387FD0D89",
    "soc": "756DF168F63F9A6341711C61AA5EC578",
    "lit": "4F431E63B9C9B25246F00AD7B5253996",
    "geo": "20E79180061DB32845C11FC7BD87C7C8",
    "eng": "4B53A6CB75B0B5E1427E596EB4931A2A",
    "ger": "B5963A8D84CF9020461EAE42F37F541F",
    "fra": "5BAC840990A3AF0A4EE80D1B5A1F9527",
    "esp": "8C65A335D93D9DA047C42613F61416F3",
    "chi": "F6298F3470D898D043E18BC680F60434",
}


def _get_proj_id_by_alias(alias: str) -> str:
    return SUBJECT_TO_PROJ_ID_MAP.get(alias, "UNKNOWN_PROJ_ID")


def _get_alias_by_official_name(official_name: str) -> str:
    return SUBJECT_ALIAS_MAP.get(official_name, "unknown")


@dataclass(frozen=True)
class SubjectInfo:
    alias: str
    official_name: str
    proj_id: str
    exam_year: int = 2026

    def __post_init__(self):
        if not self.alias or not isinstance(self.alias, str):
            raise ValueError("Alias must be a non-empty string")
        if not self.official_name or not isinstance(self.official_name, str):
            raise ValueError("Official name must be a non-empty string")
        if not self.proj_id or not isinstance(self.proj_id, str):
            raise ValueError("Project ID must be a non-empty string")
        if self.exam_year < 2000 or self.exam_year > 2100:
            raise ValueError(f"Invalid exam year: {self.exam_year}")

    @classmethod
    def from_alias(cls, alias: str) -> 'SubjectInfo':
        official_name = next((name for name, al in SUBJECT_ALIAS_MAP.items() if al == alias), None)
        if official_name is None:
            raise ValueError(f"Unknown subject alias: {alias}")
        proj_id = _get_proj_id_by_alias(alias)
        if proj_id == "UNKNOWN_PROJ_ID":
            raise ValueError(f"No proj_id found for alias: {alias}")
        return cls(alias=alias, official_name=official_name, proj_id=proj_id)

    @classmethod
    def from_official_name(cls, official_name: str) -> 'SubjectInfo':
        alias = _get_alias_by_official_name(official_name)
        if alias == "unknown":
            raise ValueError(f"Unknown official subject name: {official_name}")
        proj_id = _get_proj_id_by_alias(alias)
        if proj_id == "UNKNOWN_PROJ_ID":
            raise ValueError(f"No proj_id found for official name: {official_name}")
        return cls(alias=alias, official_name=official_name, proj_id=proj_id)

    @property
    def base_url(self) -> str:
        if not re.match(r'^[A-F0-9]+$', self.proj_id):
            raise ValueError(f"proj_id '{self.proj_id}' is not a valid hex string for URL construction.")
        encoded_proj_id = quote(self.proj_id, safe='')
        return f"https://ege.fipi.ru/bank/index.php?proj={encoded_proj_id}"

    @property
    def questions_url(self) -> str:
        if not re.match(r'^[A-F0-9]+$', self.proj_id):
            raise ValueError(f"proj_id '{self.proj_id}' is not a valid hex string for URL construction.")
        encoded_proj_id = quote(self.proj_id, safe='')
        return f"https://ege.fipi.ru/bank/questions.php?proj={encoded_proj_id}"

    @property
    def subject_name(self) -> str:
        return self.official_name

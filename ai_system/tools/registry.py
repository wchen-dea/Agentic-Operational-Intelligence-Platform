"""Default skill registry - pre-loaded with all platform skills."""

from functools import lru_cache

from ai_system.skills import SkillRegistry
from ai_system.tools.catalog import (
    DetectAnomaliesSkill,
    DiagnoseSignalsSkill,
    FetchKPISkill,
    GenerateNarrativeSkill,
    SemanticSearchSkill,
)


@lru_cache(maxsize=1)
def get_skill_registry() -> SkillRegistry:
    """Return the singleton skill registry with all skills registered."""
    reg = SkillRegistry()
    reg.register(FetchKPISkill())
    reg.register(DetectAnomaliesSkill())
    reg.register(SemanticSearchSkill())
    reg.register(DiagnoseSignalsSkill())
    reg.register(GenerateNarrativeSkill())
    return reg

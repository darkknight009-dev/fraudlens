"""Rule configuration API schemas."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RuleConfigurationUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    configuration: dict[str, Any] = Field(min_length=1)


class RuleConfigurationResponse(BaseModel):
    version: str
    configuration: dict[str, Any]

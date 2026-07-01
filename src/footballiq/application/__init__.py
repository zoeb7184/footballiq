"""Application layer — use cases and orchestration.

Coordinates domain objects to fulfil user intents (e.g. "value this
player", "compare squads"). Defines ports (interfaces) that
infrastructure implements. Depends on: kernel, domains. Never imports
infrastructure or api.
"""

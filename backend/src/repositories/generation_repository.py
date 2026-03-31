from __future__ import annotations

from uuid import UUID

from src.models.contracts import GenerationRecord, SourceReference

_GENERATIONS: dict[UUID, GenerationRecord] = {}
_SOURCES: dict[UUID, list[SourceReference]] = {}


class GenerationRepository:
    def save_generation(self, generation: GenerationRecord) -> GenerationRecord:
        _GENERATIONS[generation.generation_id] = generation
        _SOURCES[generation.generation_id] = generation.source_references
        return generation

    def save_sources(self, generation_id: UUID, sources: list[SourceReference]) -> None:
        _SOURCES[generation_id] = sources

    def get_generation(self, generation_id: UUID) -> GenerationRecord | None:
        generation = _GENERATIONS.get(generation_id)
        if generation is None:
            return None
        generation.source_references = _SOURCES.get(generation_id, [])
        return generation

    def all_generations(self) -> list[GenerationRecord]:
        records = []
        for generation in _GENERATIONS.values():
            generation.source_references = _SOURCES.get(generation.generation_id, [])
            records.append(generation)
        return records

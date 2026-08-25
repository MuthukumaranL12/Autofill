import numpy as np
from backend.form_pipeline.canonical_fields import CANONOICAL_FIELDS
from backend.models.form_models import FormField, MatchField
from sentence_transformers import SentenceTransformer


class SemanticMatcher:
    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.embeddings = self._build_canonical_embedding()
        self.threshold = 0.70

    def _build_canonical_embedding(self):
        embedding_store = {}
        for canonical_field, aliases in CANONOICAL_FIELDS.items():
            alias_embeddings = self.model.encode(
                aliases,
                convert_to_numpy=True,
                normalize_embeddings=True,
            )

            for alias, embedding in zip(aliases, alias_embeddings):
                embedding_store[alias] = {
                    "canonical_field": canonical_field,
                    "embedding": embedding,
                }
        return embedding_store

    def _match_field(self, field: FormField) -> tuple[str | None, float, str | None]:

        if not self.embeddings:
            return None, -1.0, None

        field_embedding = self.model.encode(field.normalized_label, convert_to_numpy=True, normalize_embeddings=True)

        best_match = None
        best_score = -1
        best_alias = None

        for alias, data in self.embeddings.items():
            embedding = data["embedding"]

            similarity = np.dot(field_embedding, embedding)

            if similarity > best_score:
                best_score = float(similarity)
                best_match = data["canonical_field"]
                best_alias = alias

        if best_score < self.threshold:
            return None, best_score, None

        return best_match, best_score, best_alias

    def match(self, fields: list[FormField]) -> list[MatchField]:
        matches = []
        for field in fields:
            best_match, score, best_alias = self._match_field(field)

            matched_field = MatchField(
                form_field=field,
                canonical_field=best_match,
                matched_alias=best_alias,
                similarity_score=score
            )
            matches.append(matched_field)

        return matches

    # Keep typo-compatible alias used by old callers.
    def macth(self, fields: list[FormField]) -> list[MatchField]:
        return self.match(fields)

if __name__ == "__main__":

    obj1 = SemanticMatcher()
    test_field = FormField(
        label="name",
        normalized_label="name",
        value=None,
        label_bbox=None,
        value_bbox=None,
        confidence=0.99,
        field_type="text",
        source="form",
    )
    match, score, _ = obj1._match_field(test_field)
    print(match)
    print(score)
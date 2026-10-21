from collections.abc import Mapping, Sequence

type AttributeScalar = str | bool | int | float
type AttributeValue = AttributeScalar | Sequence[AttributeScalar]
type Attributes = Mapping[str, AttributeValue]

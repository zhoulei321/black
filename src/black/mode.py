"""Data structures configuring Black behavior.

Mostly around Python language feature support per version and Black configuration
chosen by the user.
"""

import sys

from dataclasses import dataclass, field
from enum import Enum
from operator import attrgetter
from typing import Dict, Set

if sys.version_info < (3, 8):
    from typing_extensions import Final
else:
    from typing import Final

from black.const import DEFAULT_LINE_LENGTH


class TargetVersion(Enum):
    PY33 = 3
    PY34 = 4
    PY35 = 5
    PY36 = 6
    PY37 = 7
    PY38 = 8
    PY39 = 9
    PY310 = 10


class Feature(Enum):
    F_STRINGS = 2
    NUMERIC_UNDERSCORES = 3
    TRAILING_COMMA_IN_CALL = 4
    TRAILING_COMMA_IN_DEF = 5
    # The following two feature-flags are mutually exclusive, and exactly one should be
    # set for every version of python.
    ASYNC_IDENTIFIERS = 6
    ASYNC_KEYWORDS = 7
    ASSIGNMENT_EXPRESSIONS = 8
    POS_ONLY_ARGUMENTS = 9
    RELAXED_DECORATORS = 10
    PATTERN_MATCHING = 11
    UNPACKING_ON_FLOW = 12
    ANN_ASSIGN_EXTENDED_RHS = 13
    FORCE_OPTIONAL_PARENTHESES = 50

    # __future__ flags
    FUTURE_ANNOTATIONS = 51


FUTURE_FLAG_TO_FEATURE: Final = {
    "annotations": Feature.FUTURE_ANNOTATIONS,
}


VERSION_TO_FEATURES: Dict[TargetVersion, Set[Feature]] = {
    TargetVersion.PY33: {Feature.ASYNC_IDENTIFIERS},
    TargetVersion.PY34: {Feature.ASYNC_IDENTIFIERS},
    TargetVersion.PY35: {Feature.TRAILING_COMMA_IN_CALL, Feature.ASYNC_IDENTIFIERS},
    TargetVersion.PY36: {
        Feature.F_STRINGS,
        Feature.NUMERIC_UNDERSCORES,
        Feature.TRAILING_COMMA_IN_CALL,
        Feature.TRAILING_COMMA_IN_DEF,
        Feature.ASYNC_IDENTIFIERS,
    },
    TargetVersion.PY37: {
        Feature.F_STRINGS,
        Feature.NUMERIC_UNDERSCORES,
        Feature.TRAILING_COMMA_IN_CALL,
        Feature.TRAILING_COMMA_IN_DEF,
        Feature.ASYNC_KEYWORDS,
        Feature.FUTURE_ANNOTATIONS,
    },
    TargetVersion.PY38: {
        Feature.F_STRINGS,
        Feature.NUMERIC_UNDERSCORES,
        Feature.TRAILING_COMMA_IN_CALL,
        Feature.TRAILING_COMMA_IN_DEF,
        Feature.ASYNC_KEYWORDS,
        Feature.FUTURE_ANNOTATIONS,
        Feature.ASSIGNMENT_EXPRESSIONS,
        Feature.POS_ONLY_ARGUMENTS,
        Feature.UNPACKING_ON_FLOW,
        Feature.ANN_ASSIGN_EXTENDED_RHS,
    },
    TargetVersion.PY39: {
        Feature.F_STRINGS,
        Feature.NUMERIC_UNDERSCORES,
        Feature.TRAILING_COMMA_IN_CALL,
        Feature.TRAILING_COMMA_IN_DEF,
        Feature.ASYNC_KEYWORDS,
        Feature.FUTURE_ANNOTATIONS,
        Feature.ASSIGNMENT_EXPRESSIONS,
        Feature.RELAXED_DECORATORS,
        Feature.POS_ONLY_ARGUMENTS,
        Feature.UNPACKING_ON_FLOW,
        Feature.ANN_ASSIGN_EXTENDED_RHS,
    },
    TargetVersion.PY310: {
        Feature.F_STRINGS,
        Feature.NUMERIC_UNDERSCORES,
        Feature.TRAILING_COMMA_IN_CALL,
        Feature.TRAILING_COMMA_IN_DEF,
        Feature.ASYNC_KEYWORDS,
        Feature.FUTURE_ANNOTATIONS,
        Feature.ASSIGNMENT_EXPRESSIONS,
        Feature.RELAXED_DECORATORS,
        Feature.POS_ONLY_ARGUMENTS,
        Feature.UNPACKING_ON_FLOW,
        Feature.ANN_ASSIGN_EXTENDED_RHS,
        Feature.PATTERN_MATCHING,
    },
}


def supports_feature(target_versions: Set[TargetVersion], feature: Feature) -> bool:
    return all(feature in VERSION_TO_FEATURES[version] for version in target_versions)


@dataclass
class Mode:
    target_versions: Set[TargetVersion] = field(default_factory=set)
    line_length: int = DEFAULT_LINE_LENGTH
    string_normalization: bool = True
    is_pyi: bool = False
    is_ipynb: bool = False
    magic_trailing_comma: bool = True
    experimental_string_processing: bool = False
    python_cell_magics: Set[str] = field(default_factory=set)

    def get_cache_key(self) -> str:
        if self.target_versions:
            version_str = ",".join(
                str(version.value)
                for version in sorted(self.target_versions, key=attrgetter("value"))
            )
        else:
            version_str = "-"
        parts = [
            version_str,
            str(self.line_length),
            str(int(self.string_normalization)),
            str(int(self.is_pyi)),
            str(int(self.is_ipynb)),
            str(int(self.magic_trailing_comma)),
            str(int(self.experimental_string_processing)),
            ",".join(sorted(self.python_cell_magics)),
        ]
        return ".".join(parts)

import anonlink.typechecking as _typechecking

def greedy_solve_native(candidates: _typechecking.CandidatePairs) -> _typechecking.MatchGroups: ...
def probabilistic_greedy_solve_native(
    candidates: _typechecking.CandidatePairs,
    *,
    merge_threshold: float = ...,
    deduplicated: bool = ...) -> _typechecking.MatchGroups: ...

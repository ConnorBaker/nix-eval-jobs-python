from pydantic.alias_generators import to_camel

from nix_eval_jobs.extra_pydantic import PydanticObject


class NixEvalStats(PydanticObject, alias_generator=to_camel):
    class NixEvalStatsEnvs(PydanticObject, alias_generator=to_camel):
        bytes: int
        elements: int
        number: int

    class NixEvalStatsGc(PydanticObject, alias_generator=to_camel):
        cycles: int
        heap_size: int
        total_bytes: int

    class NixEvalStatsList(PydanticObject, alias_generator=to_camel):
        bytes: int
        concats: int
        elements: int

    class NixEvalStatsSets(PydanticObject, alias_generator=to_camel):
        bytes: int
        elements: int
        number: int

    class NixEvalStatsSizes(PydanticObject, alias_generator=to_camel):
        Attr: int
        Bindings: int
        Env: int
        Value: int

    class NixEvalStatsSymbols(PydanticObject, alias_generator=to_camel):
        bytes: int
        number: int

    class NixEvalStatsTime(PydanticObject, alias_generator=to_camel):
        cpu: float
        gc: float
        gc_fraction: float

    class NixEvalStatsValues(PydanticObject, alias_generator=to_camel):
        bytes: int
        number: int

    cpu_time: float
    envs: NixEvalStatsEnvs
    gc: NixEvalStatsGc
    list: NixEvalStatsList
    nr_avoided: int
    nr_exprs: int
    nr_function_calls: int
    nr_lookups: int
    nr_op_update_values_copied: int
    nr_op_updates: int
    nr_prim_op_calls: int
    nr_thunks: int
    sets: NixEvalStatsSets
    sizes: NixEvalStatsSizes
    symbols: NixEvalStatsSymbols
    time: NixEvalStatsTime
    values: NixEvalStatsValues

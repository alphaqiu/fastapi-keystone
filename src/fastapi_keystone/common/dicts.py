"""字典相关工具函数"""

import copy


def deep_merge(dct, merge_dct):
    """
    Recursively merge two dictionaries, returning a new dict.
    The original dicts are not modified.

    Args:
        dct (dict): The destination dictionary to merge into.
        merge_dct (dict): The source dictionary to merge from.

    Returns:
        dict: The merged dictionary.

    Example:
        >>> a = {"a": 1, "b": {"c": 2}}
        >>> b = {"b": {"d": 3}, "e": 4}
        >>> deep_merge(a, b)
        {'a': 1, 'b': {'c': 2, 'd': 3}, 'e': 4}
    """
    result = copy.deepcopy(dct)
    for k, v in merge_dct.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = deep_merge(result[k], v)
        else:
            result[k] = copy.deepcopy(v)
    return result

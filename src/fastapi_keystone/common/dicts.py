"""字典相关工具函数"""


def deep_merge(dct, merge_dct):
    """
    Recursively merge two dictionaries.

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
    for k, v in merge_dct.items():
        if (
            k in dct
            and isinstance(dct[k], dict)
            and isinstance(v, dict)
        ):
            deep_merge(dct[k], v)
        else:
            dct[k] = v
    return dct

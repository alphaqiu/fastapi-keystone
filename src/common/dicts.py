"""字典相关工具函数"""


def deep_merge(base: dict, update: dict) -> dict:
    """深度合并两个字典"""
    merged = base.copy()
    for key, value in update.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged

# core模块初始化
# 注意：speech、code、interview模块已被删除，相关功能已迁移到skill_library_manager
# 请通过API调用使用相关功能

from .skill import update_skill_profile

__all__ = [
    "update_skill_profile"
]


# 替换前（MySQL版本）
# from .skill_profile import update_skill_profile, get_db_connection

# 替换后（JSON版本）
from .skill_profile_json import update_skill_profile, get_skill_profile

__all__ = ["update_skill_profile", "get_skill_profile"]
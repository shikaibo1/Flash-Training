# core/skill/skill_profile_json.py
import json
import os

# 技能档案存储路径（自动创建data目录）
SKILL_PROFILE_PATH = "data/skill_profiles.json"
os.makedirs(os.path.dirname(SKILL_PROFILE_PATH), exist_ok=True)

# 初始化空档案（首次运行自动创建）
if not os.path.exists(SKILL_PROFILE_PATH):
    with open(SKILL_PROFILE_PATH, "w", encoding="utf-8") as f:
        json.dump({}, f)


def load_skill_profiles() -> dict:
    """加载所有用户的技能档案（内部函数）"""
    try:
        with open(SKILL_PROFILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"加载技能档案失败：{e}")
        return {}


def save_skill_profiles(profiles: dict) -> bool:
    """保存技能档案到文件（内部函数）"""
    try:
        with open(SKILL_PROFILE_PATH, "w", encoding="utf-8") as f:
            json.dump(profiles, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存技能档案失败：{e}")
        return False


def update_skill_profile(user_id: str, skill_name: str, score: int) -> int:
    """更新用户技能档案，返回新难度（1-10级）"""
    profiles = load_skill_profiles()

    # 初始化用户/技能档案
    if user_id not in profiles:
        profiles[user_id] = {}
    if skill_name not in profiles[user_id]:
        profiles[user_id][skill_name] = {
            "last_score": 0,
            "difficulty": 1,
            "practice_count": 0
        }

    # 计算新难度（评分0-100映射为1-10级）
    new_difficulty = min(max(1, round(score / 10)), 10)
    # 更新档案字段
    profiles[user_id][skill_name]["last_score"] = score
    profiles[user_id][skill_name]["difficulty"] = new_difficulty
    profiles[user_id][skill_name]["practice_count"] += 1

    # 保存更新
    if save_skill_profiles(profiles):
        print(f"✅ 更新用户{user_id}【{skill_name}】难度为{new_difficulty}级")
        return new_difficulty
    else:
        print(f"❌ 更新用户{user_id}技能档案失败")
        return 1


# ========== 补充原有__init__.py需要的get_skill_profile函数 ==========
def get_skill_profile(user_id: str) -> dict:
    """获取单个用户的技能档案（适配原有导入逻辑）"""
    all_profiles = load_skill_profiles()
    # 返回该用户的档案，无则返回空字典
    user_profile = all_profiles.get(user_id, {})
    print(f"✅ 已获取用户{user_id}的技能档案：{user_profile}")
    return user_profile
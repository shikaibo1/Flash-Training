# examples/unified_system_example.py
"""
统一技能训练系统使用示例
展示如何使用新的原子技能、技能库和统一练习管理器
"""

from core.skill.atomic_skill_manager import atomic_skill_manager
from core.skill.skill_library_manager import skill_library_manager
from core.practice.unified_practice_manager import unified_practice_manager


def example_usage():
    print("=== 闪练AI统一技能训练系统演示 ===\n")

    # 1. 展示现有原子技能
    print("1. 现有原子技能：")
    existing_atomic_skills = atomic_skill_manager.load_atomic_skills()
    for skill in existing_atomic_skills:
        print(f"   - {skill['name']}: {skill['description']}")
    print()

    # 2. 添加新的原子技能（如果需要）
    print("2. 添加新的原子技能示例：")
    new_atomic_skill = atomic_skill_manager.add_atomic_skill(
        name="创新思维",
        description="能够提出新颖独特的想法和解决方案",
        categories=["创意", "创新"]
    )
    print(f"   新增原子技能: {new_atomic_skill['name']}")
    print()

    # 3. 展示现有技能库
    print("3. 现有技能库：")
    existing_skills = skill_library_manager.get_enabled_skills()
    for skill in existing_skills:
        print(f"   - {skill['display_name']}: {skill['description']}")
    print()

    # 4. 添加自定义技能
    print("4. 添加自定义技能示例：")
    custom_skill = skill_library_manager.add_custom_skill(
        name="Presentation",
        display_name="演示汇报",
        description="提升演示汇报和公众表达能力",
        generate_prompt="你是演示教练，请生成一个适合练习的演示主题，要求：场景：{scene}，时长：{duration}，要点：{key_points}。只需输出主题，无需其他内容。",
        evaluate_prompt="你是演示专家，评估以下演示内容：\n\n演示内容：{content}\n\n要求：从内容准确性、结构完整性、表达清晰度等方面进行评估，并按以下格式输出：总分(1-10分)|各项得分详情|优点|改进建议。",
        atomic_skills=["as_001", "as_002", "as_003"],  # 内容准确性、结构完整性、表达清晰度
        default_params={
            "scene": "工作汇报",
            "duration": "5分钟",
            "key_points": ""
        }
    )
    print(f"   新增自定义技能: {custom_skill['display_name']}")
    print()

    # 5. 生成技能内容示例
    print("5. 为演讲技能生成练习内容：")
    speech_content = skill_library_manager.generate_skill_content(
        skill_id="skill_speech",
        scene="产品发布",
        duration="3分钟",
        keyword="创新"
    )
    print(f"   生成的演讲主题: {speech_content}")
    print()

    # 6. 评估示例内容
    print("6. 评估示例演讲内容：")
    sample_speech = "尊敬的各位领导、同事们，大家好！今天我要分享的是我们团队最新研发的创新产品。这款产品采用了先进的技术，能够显著提升工作效率。它具有三个核心优势：第一，高效性；第二，稳定性；第三，易用性。通过我们的产品，相信能够为大家的工作带来极大的便利。谢谢大家！"
    evaluation_result = skill_library_manager.evaluate_skill_content(
        skill_id="skill_speech",
        content=sample_speech,
        reference="产品发布主题，3分钟演讲"
    )
    print(f"   评分: {evaluation_result['score']}")
    print(f"   优点: {evaluation_result['strengths'][0]}")
    print(f"   改进建议: {evaluation_result['improvements'][0]}")
    print()

    # 7. 开始练习会话示例
    print("7. 开始演讲练习会话：")
    user_id = "user_123"
    practice_session = unified_practice_manager.start_practice_session(
        user_id=user_id,
        skill_id="skill_speech",
        scene="商务谈判",
        duration="5分钟"
    )
    if not practice_session["error"]:
        session_id = practice_session["data"]["session_id"]
        question = practice_session["data"]["question"]
        print(f"   练习会话ID: {session_id}")
        print(f"   练习题目: {question}")

        # 提交示例答案
        sample_answer = "在商务谈判中，关键是建立信任和找到双赢方案。我认为可以从三个方面入手：第一，充分准备，了解对方需求；第二，展现专业素养和诚信；第三，灵活应对，寻求共同利益点。这样的策略能够促成成功的合作。"
        submission_result = unified_practice_manager.submit_answer(
            user_id=user_id,
            session_id=session_id,
            answer=sample_answer
        )

        if not submission_result["error"]:
            print(f"   评估评分: {submission_result['data']['evaluation_result']['score']}")
            print(f"   优点: {submission_result['data']['evaluation_result']['strengths'][0]}")
            print(f"   改进建议: {submission_result['data']['evaluation_result']['improvements'][0]}")
    print()

    # 8. 获取用户练习历史
    print("8. 获取用户练习历史：")
    user_history = unified_practice_manager.get_user_practice_history(user_id=user_id)
    print(f"   该用户共有 {len(user_history)} 次练习记录")

    # 9. 获取技能进步情况
    print("9. 获取技能进步情况：")
    progress = unified_practice_manager.get_skill_progress(user_id=user_id, skill_id="skill_speech")
    print(f"   演讲技能总练习次数: {progress['total_sessions']}")
    print(f"   完成练习次数: {progress['completed_sessions']}")
    print()
    if progress['completed_sessions'] > 0:
        print(f"   平均评分: {progress['avg_score']}")
        print(f"   最新评分: {progress['latest_score']}")


if __name__ == "__main__":
    example_usage()
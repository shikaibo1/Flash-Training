# main.py
import time
import json
import os
import datetime
# ========== 适配你的文件结构的导入 ==========
from utils.logger import logger
from config.base_config import DEFAULT_CONFIG
# 核心业务模块导入
# from core.speech.speech_evaluator import evaluate_speech_draft, format_speech_evaluation
# from core.code.code_evaluator import evaluate_python_code
# from core.speech.topic_generator import generate_speech_topic
# from core.code.feedback_generator import generate_code_feedback
from core.skill.skill_profile_json import (
    update_skill_profile,
    load_skill_profiles  # 新增：加载档案用于查询反馈
)
# from core.interview.agent_evaluator import (
#     generate_random_interview_question,
#     evaluate_interview_answer,
#     format_evaluation_result
# )


# ========== 通用工具函数 ==========
def save_to_file(content, filename_prefix):
    """通用保存文件函数（统一反馈保存逻辑）"""
    timestamp = time.strftime("%Y%m%d%H%M%S")
    filename = f"{filename_prefix}_{timestamp}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    return filename


# ========== 微技能菜单展示 ==========
def show_menu():
    """展示微技能选择菜单"""
    print("\n===== 闪练AI - 碎片化技能练习平台 =====")
    print("请选择你要练习的微技能（输入对应数字）：")
    print("1. 面试模拟（AI随机出题+多智能体评分）")
    print("2. 演讲话题生成（自定义场景/难度/时长+草稿点评）")
    print("3. 代码反馈（Python代码校验+分步解析+优化对比）")
    print("4. 历史记录查看（所有保存的TXT点评）")
    print("0. 退出程序")


# ========== 1. 面试模拟模块（原有逻辑，保留） ==========
def run_interview_module():
    """面试模拟模块（完整输入反馈）"""
    print("\n----- 面试模拟模块 -----")
    # 1. 用户输入（岗位类型）
    job_type = input(f"请输入面试岗位类型（默认：{DEFAULT_CONFIG['default_job_type']}）：").strip()
    job_type = job_type if job_type else DEFAULT_CONFIG['default_job_type']

    # 2. 生成问题（反馈）
    print(f"\n正在为【{job_type}】岗位生成随机面试问题...")
    question = generate_random_interview_question(job_type)
    print(f"✅ 面试问题：{question}")

    # 3. 用户输入（面试回答）
    answer = input("\n请输入你的面试回答：").strip()
    if not answer:
        answer = f"我对{job_type}岗位的核心技能有基础掌握，能完成相关工作任务。"
        print(f"⚠️ 未输入回答，使用默认回答：{answer}")

    # 4. 智能体评分（详细反馈）
    print("\n智能体正在评分，请稍候...")
    evaluation = evaluate_interview_answer(question, answer, job_type)
    formatted_result = format_evaluation_result(evaluation)  # 改造后的格式化函数
    print(formatted_result)

    # 5. 反馈保存（用户选择）
    save_choice = input("\n是否保存评价结果到文件？（y/n，默认n）：").strip().lower()
    if save_choice == "y":
        filename = save_to_file(formatted_result, f"面试评价_{job_type}")
        print(f"✅ 结果已保存到：{filename}")


# ========== 2. 演讲话题模块（新增丰富输入反馈） ==========
# def run_speech_module():
#     """演讲话题生成模块（多智能体点评版）"""
#     print("\n----- 演讲话题生成模块 -----")
#     # 1. 多维度用户输入（原有逻辑不变）
#     scene = input(f"请输入演讲场景（默认：{DEFAULT_CONFIG['default_speech_scene']}）：").strip()
#     difficulty = input(f"请输入难度（入门/进阶/高阶，默认：{DEFAULT_CONFIG['default_speech_difficulty']}）：").strip()
#     duration = input("请输入演讲时长（如30秒/2分钟，默认：30秒）：").strip()
#     keyword = input("请输入核心关键词（如职场沟通/团队协作，选填）：").strip()

#     # 补全默认值（原有逻辑不变）
#     scene = scene if scene else DEFAULT_CONFIG['default_speech_scene']
#     difficulty = difficulty if difficulty else DEFAULT_CONFIG['default_speech_difficulty']
#     duration = duration if duration else "30秒"

#     # 2. 生成个性化话题（原有逻辑不变）
#     print(f"\n正在生成【{scene}】场景-{difficulty}难度-{duration}的演讲话题（关键词：{keyword or '无'}）...")
#     topics = []
#     for i in range(3):
#         topic = generate_speech_topic(difficulty, scene)
#         if keyword:
#             topic = f"{topic}（核心：{keyword}）"
#         topics.append(f"{i + 1}. {topic}")

#     print("\n🎤 为你生成以下演讲话题（请选择1个，或直接使用）：")
#     for t in topics:
#         print(f"   {t}")

#     topic_choice = input("\n请选择话题序号（1/2/3，默认1）：").strip()
#     try:
#         selected_topic = topics[int(topic_choice) - 1] if topic_choice and int(topic_choice) in [1, 2, 3] else topics[0]
#     except:
#         selected_topic = topics[0]
#     print(f"\n✅ 你选择的话题：{selected_topic}")

#     # 3. 输入演讲草稿，使用多智能体点评（核心修改）
#     draft_choice = input("\n是否输入演讲草稿获取AI多智能体点评？（y/n，默认n）：").strip().lower()

    # main.py - 演讲模块
    # def run_speech_module():
    #     # （保留原有输入逻辑：scene/difficulty/duration/keyword/topic选择/草稿输入）
    #     if draft_choice == "y":
    #         draft = input("请输入你的演讲草稿（100字以内）：").strip()
    #         if not draft:
    #             draft = f"大家好，今天我想分享{selected_topic}的心得，核心是做好沟通和执行。"
    #             print(f"⚠️ 未输入草稿，使用默认草稿：{draft}")

    #         print("\n🎯 多智能体正在点评你的演讲草稿，请稍候...")
    #         # 调用改造后的评价函数（返回统一字段）
    #         evaluation_result = evaluate_speech_draft(
    #             draft=draft, scene=scene, duration=duration, keyword=keyword
    #         )
    #         # 格式化展示（适配统一字段）
    #         formatted_feedback = format_speech_evaluation(evaluation_result)
    #         print(formatted_feedback)

    #         # 保存逻辑（保留，自动包含统一字段）
    #         save_choice = input("\n是否保存话题+草稿+多智能体点评？（y/n，默认n）：").strip().lower()
    #         if save_choice == "y":
    #             content = f"演讲场景：{scene}\n难度：{difficulty}\n时长：{duration}\n选择的话题：{selected_topic}\n演讲草稿：{draft}\n\n{formatted_feedback}"
    #             filename = save_to_file(content, f"演讲多智能体点评_{scene}")
    #             print(f"✅ 内容已保存到：{filename}")

# ========== 3. 代码反馈模块（新增丰富输入反馈） ==========
# main.py - 代码模块
# main.py - 代码反馈模块（f-string三引号格式化，适配统一字段）
# def run_code_module():
#     print("\n----- 代码反馈模块 -----")
#     print("提示：请输入Python代码（如 nums = [1,2,3]; print([x*2 for x in nums])）")
#     user_code = input("请输入你的Python代码：").strip()

#     # 补全默认代码
#     if not user_code:
#         user_code = "nums = [1,2,3]; print([x*2 for x in nums])"
#         print(f"⚠️ 未输入代码，使用测试代码：{user_code}")

#     # 选择优化方向
#     optimize_type = input("请选择优化方向（语法/逻辑/性能/规范，默认：语法）：").strip().lower()
#     optimize_type = optimize_type if optimize_type in ["语法", "逻辑", "性能", "规范"] else "语法"

#     print(f"\n正在分析代码（优化方向：{optimize_type}），检测问题并生成优化方案...")
#     # 调用代码评价函数（返回统一字段：score/strengths/improvements/aiComment）
#     code_result = evaluate_python_code(user_code=user_code, optimize_type=optimize_type)

#     # ========== 你想要的f-string三引号格式化（核心） ==========
#     formatted_feedback = f"""
# 🔍 Python代码评价结果（优化方向：{optimize_type}）
# =========================================
# 【原始代码】
# {code_result['original_code']}

# 📊 综合评分：{code_result['score']}/10分

# ✨ 核心优点：
# {chr(10).join([f"{idx + 1}. {s}" for idx, s in enumerate(code_result['strengths'])])}

# 📈 待改进点：
# {chr(10).join([f"{idx + 1}. {imp}" for idx, imp in enumerate(code_result['improvements'])])}

# 💡 AI综合评语：
# {code_result['aiComment']}

# 🔧 优化后代码：
# {code_result['optimized_code']}
#     """
#     print(formatted_feedback)

#     # 保存结果
#     save_choice = input("\n是否保存代码+分析+优化结果？（y/n，默认n）：").strip().lower()
#     if save_choice == "y":
#         content = formatted_feedback.strip()
#         filename = save_to_file(content, f"代码反馈_{optimize_type}")
#         print(f"✅ 内容已保存到：{filename}")


# ========== 4. 技能档案模块（新增丰富输入反馈） ==========
# main.py - 4号模块：历史点评记录查看（替换原技能档案）
def run_history_module():
    """历史记录查看模块：读取并展示所有保存的演讲/代码/面试点评TXT文件"""
    print("\n===== 历史点评记录查看 =====")
    # 定义需要筛选的点评文件前缀（匹配之前的保存命名规则）
    TARGET_PREFIXES = ("演讲点评_", "代码反馈_", "面试点评_")
    # 获取当前项目根目录（和保存的TXT同目录）
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # 遍历目录，筛选符合条件的TXT文件
    history_files = []
    for file in os.listdir(base_dir):
        # 筛选：以指定前缀开头 + 以.txt结尾
        if file.startswith(TARGET_PREFIXES) and file.endswith(".txt"):
            file_path = os.path.join(base_dir, file)
            # 获取文件最后修改时间（时间戳转格式化字符串）
            modify_time = os.path.getmtime(file_path)
            format_time = datetime.datetime.fromtimestamp(modify_time).strftime("%Y-%m-%d %H:%M")
            history_files.append({
                "name": file,
                "path": file_path,
                "modify_time": format_time
            })

    # 无历史记录的情况
    if not history_files:
        print("📂 暂无保存的点评历史记录（演讲/代码/面试）")
        input("\n按回车键返回主菜单...")
        return

    # 按【最新修改时间倒序】排序（核心：最新保存的在最前面）
    history_files.sort(key=lambda x: x["modify_time"], reverse=True)

    # 循环展示记录列表，支持多次查看
    while True:
        print("\n📂 已保存的点评记录（按最新修改排序，共{}条）：".format(len(history_files)))
        print("-" * 80)
        # 打印序号+文件名+修改时间
        for idx, f in enumerate(history_files, 1):
            print(f"{idx:2d}. {f['name']} | 保存时间：{f['modify_time']}")
        print("-" * 80)
        print("输入「记录序号」查看详情 | 输入「0」返回主菜单")

        # 获取用户选择，处理异常输入
        try:
            choice = input("\n请输入你的选择：").strip()
            if choice == "0":
                print("🔙 返回主菜单...")
                break  # 退出循环，返回主菜单
            choice_idx = int(choice) - 1
            # 校验序号范围
            if 0 <= choice_idx < len(history_files):
                selected_file = history_files[choice_idx]
                # 读取并展示文件内容
                print(f"\n===== 查看记录：{selected_file['name']} =====")
                try:
                    # 以UTF-8编码读取，避免中文乱码
                    with open(selected_file["path"], "r", encoding="utf-8") as f:
                        content = f.read()
                    print(content)
                except Exception as e:
                    print(f"❌ 读取文件失败：{str(e)}")
                # 看完后等待回车，返回列表
                input("\n按回车键返回记录列表...")
            else:
                print(f"❌ 请输入1-{len(history_files)}之间的序号！")
        except ValueError:
            print("❌ 输入无效！请输入数字序号（0-{}）".format(len(history_files)))


# 若原有代码中有run_skill_module函数，直接删除即可


# ========== 主程序逻辑 ==========
def main():
    """交互式主程序：自选微技能+完整输入反馈"""
    logger.info("闪练AI启动，进入交互式菜单模式")
    while True:
        # 展示菜单
        show_menu()
        # 用户选择模块
        choice = input("\n请输入选择的数字：").strip()

        # 执行对应模块
        if choice == "1":
            run_interview_module()
        elif choice == "2":
            run_speech_module()
        elif choice == "3":
            run_code_module()
        elif choice == "4":
            run_history_module()
        elif choice == "0":
            print("\n👋 感谢使用闪练AI，程序已退出！")
            logger.info("用户主动退出程序")
            break
        else:
            print("\n❌ 输入无效，请选择0-4之间的数字！")

        # 执行完模块后，询问是否继续
        continue_choice = input("\n是否继续练习其他微技能？（y/n，默认y）：").strip().lower()
        if continue_choice != "y" and continue_choice != "":
            print("\n👋 感谢使用闪练AI，程序已退出！")
            logger.info("用户选择退出程序")
            break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("用户中断程序运行")
        print("\n\n👋 程序已被中断，感谢使用！")
    except Exception as e:
        logger.error(f"程序运行出错：{e}", exc_info=True)
        print(f"\n❌ 程序运行出错：{str(e)}，请查看日志文件！")
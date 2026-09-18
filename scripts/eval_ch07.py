"""ch07 摘要 prompt 标注样例验证(纯 Prompt 任务以 eval 代 TDD)。需聊天上游可调通。
断言:严格 JSON(structured output 保证)、关键事实保留、无编造实体、长度达标、寒暄不留。
用法:uv run python -m scripts.eval_ch07"""
import asyncio
import re

from app.core.summarizer import summarize_dialog

# 样例1:事实保留——订单号/手机号/诉求必须进摘要
CASE1_DIALOG = """用户:你好在吗
客服:您好,我是槐花,请问有什么能帮您?
用户:我买的智能香薰机订单1001一直没到,什么时候发货
客服:订单1001已从杭州仓发出,预计后天到。
用户:太慢了,我手机13800138000,到了让快递提前打电话
客服:好的,已备注让快递员派送前致电13800138000。
用户:对了这个香薰机水箱多大
客服:这款香薰机水箱容量300毫升。"""
CASE1_MUST = ["1001", "13800138000", "香薰机"]
CASE1_BAN = ["在吗", "您好,我是槐花"]          # 寒暄不留

# 样例2:无编造——摘要里的数字实体必须都在原文出现过
CASE2_DIALOG = """用户:订单2002能退吗
客服:订单2002是药王茶,已签收3天,符合7天无理由,可以退。
用户:那我要退,原因是买重复了
客服:好的,已为您记录退款诉求:订单2002,原因「买重复了」。"""

# 样例3:滚动合并——旧摘要里的事实不得丢
CASE3_OLD = "用户问过订单1001(智能香薰机)物流,留了手机13800138000要求快递先打电话;问过水箱容量(300毫升)。"
CASE3_DIALOG = """用户:香薰机到了,但是少了一个电源适配器
客服:非常抱歉!可为您补发适配器,或整单退货,您选哪种?
用户:补发吧
客服:好的,已登记订单1001补发适配器,3天内发出。"""
CASE3_MUST = ["1001", "13800138000", "适配器"]    # 旧事实(手机号)+ 新事实(补发适配器)


def check(name: str, summary: str, must=(), ban=(), src_digits: str = "") -> bool:
    ok = True
    problems = []
    if not (20 <= len(summary) <= 250):
        ok, problems = False, problems + [f"长度{len(summary)}出界[20,250]"]
    for kw in must:
        if kw not in summary:
            ok, problems = False, problems + [f"关键事实丢失:{kw}"]
    for kw in ban:
        if kw in summary:
            ok, problems = False, problems + [f"寒暄残留:{kw}"]
    if src_digits:
        src_nums = set(re.findall(r"\d{4,}", src_digits))
        for n in set(re.findall(r"\d{4,}", summary)):
            if n not in src_nums:
                ok, problems = False, problems + [f"编造数字实体:{n}"]
    print(f"{'✅' if ok else '❌'} {name} len={len(summary)}")
    print(f"   摘要:{summary}")
    if problems:
        print(f"   问题:{problems}")
    return ok


async def main():
    results = []
    s1 = await summarize_dialog("", CASE1_DIALOG)
    results.append(check("样例1 事实保留+寒暄不留", s1, must=CASE1_MUST, ban=CASE1_BAN,
                         src_digits=CASE1_DIALOG))
    s2 = await summarize_dialog("", CASE2_DIALOG)
    results.append(check("样例2 无编造(数字实体⊆原文)", s2, must=["2002"],
                         src_digits=CASE2_DIALOG))
    s3 = await summarize_dialog(CASE3_OLD, CASE3_DIALOG)
    results.append(check("样例3 滚动合并旧事实不丢", s3, must=CASE3_MUST,
                         src_digits=CASE3_OLD + CASE3_DIALOG))
    print(f"\n{sum(results)}/{len(results)} 通过")
    raise SystemExit(0 if all(results) else 1)


if __name__ == "__main__":
    asyncio.run(main())

'''这个文档是程序入口，框架函数
'''
import argparse
from datetime import datetime
from dateutil.parser import parse as dateParser

from processor import Processor
import utils

def main_loop(proc: Processor, start_time: datetime = None, end_time: datetime = None, equipments: str = "ABGH"):
    '''主循环，每次查找 10000 条记录后，自动换下一批
    '''

    # 在 Request 参数中设定时间，设备这些参数
    if end_time is None:
        if start_time is None:
            start_time = datetime.now().replace(hour=0, minute=0, second=0)
        end_time = start_time.replace(hour=23, minute=59, second=59)
    equip_param = utils.get_equip_param(equipments)

    proc.updateField("StartTime", utils.datetime2Str(start_time))
    proc.updateField("EndTime", utils.datetime2Str(end_time))
    proc.updateField("EquipmentId", equip_param)

    results = []
    while True:
        # 查询一批，如果超过 10000 条上限，系统会返回时间最近的一批记录
        print(proc.getField("StartTime"), "---", proc.getField("EndTime"))
        dom = proc.fetch()
        rows = proc.parseRows(dom)

        # 从新获取到的内容里去重，线性时间复杂度，然后添加到全部记录结果`results`里
        # 如果全部重复，则证明查询结束
        cut_index = utils.compare_rows(results, rows)
        if cut_index == len(rows):
            print(f"* Done. Fetched {len(results)} records")
            break

        print(f"* Add {len(rows) - cut_index} new records.")
        results.extend(rows[cut_index: ])

        # 把本次获取到的结果里最早的时间，设置成下一次查询的结束时间
        # 会有一部分的重叠，所以需要先前的去重步骤
        last_datetime = proc.parseLastDateTime(dom)
        new_endtime_str = utils.datetime2Str(last_datetime)
        proc.updateField("EndTime", new_endtime_str)

    # 保存 Excel 文件到`./results`目录下，文件名为时间区间，精确到秒
    pattern = "%Y%m%d-%H%M%S"
    str_start = utils.datetime2Str(start_time, pattern)
    str_end = utils.datetime2Str(end_time, pattern)

    save_filename = f"{str_start}__{str_end}"
    save_filename += ".xlsx"

    utils.save_xlsx(
        header=proc.parseHeader(proc.last_dom),
        rows=results,
        filename=save_filename
    )

def __main__():
    # 从参数中提取`"--start"`和`"--end"`时间参数
    parser = argparse.ArgumentParser()

    parser.add_argument("--start", type=str, required=False, help='e.g., "20201201-103000"')
    parser.add_argument("--end", type=str, required=False, help='e.g., "20201201-235959"')
    parser.add_argument("--equipments", type=str, default="ABGH", help='e.g., "ABGH"')


    args = parser.parse_args()
    start = dateParser(args.start) if args.start else None
    end = dateParser(args.end) if args.end else None

    # 开始循环
    proc = Processor()
    main_loop(proc, start, end, args.equipments)

if __name__ == "__main__":
    __main__()

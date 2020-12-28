'''这个文档是程序入口，框架函数
'''
import argparse
from datetime import datetime, timedelta
from dateutil.parser import parse as dateParser

from processor import Processor
import utils

RESULT_UPPER_LIMIT = 60000

def main_loop(proc: Processor,
              start_time: datetime = None,
              end_time: datetime = None,
              equipment: str = "ABGH",
              delta: timedelta = None,
              save_filename: str = None,
              split_size: int = 100000
              ):
    '''主循环，每次查找 10000 条记录后，自动换下一批
    '''
    # 在 Request 参数中设定时间，设备这些参数
    if end_time is None:
        if start_time is None:
            start_time = datetime.now().replace(hour=0, minute=0, second=0)
        end_time = datetime.now().replace(hour=23, minute=59, second=59)
    else:
        assert start_time, "Please enter a '--start' argument, "\
            "e.g., 'python ./main.py --start 20201215-003000'"

    if save_filename is None:
        pattern = "%Y%m%d-%H%M%S"
        str_start = utils.datetime2Str(start_time, pattern)
        str_end = utils.datetime2Str(end_time, pattern)
        save_filename = f"{str_start}__{str_end}__{equipment}"
        save_filename += ".xlsx"

    print("---------------------------")
    print("Start Time:", start_time)
    print("End Time:", end_time)
    print("Equipment:", equipment)
    print("Save File:", save_filename)
    print("---------------------------")

    assert len(equipment) == 1, f"Only fetch one equipment once. (Received: {equipment})"
    equip_param = utils.get_equip_param(equipment)

    proc.updateField("StartTime", utils.datetime2Str(start_time))
    proc.updateField("EndTime", utils.datetime2Str(end_time))
    proc.updateField("EquipmentId", equip_param)


    end_search_time = end_time
    start_search_time = max(start_time, end_time - delta)

    results = []
    while True:
        # 查询一次，查询时间长度为`delta_hours`
        proc.updateField("StartTime", utils.datetime2Str(start_search_time))
        proc.updateField("EndTime", utils.datetime2Str(end_search_time))
        print(proc.getField("StartTime"), "---", proc.getField("EndTime"))

        dom = proc.fetch()
        rows = proc.parseRows(dom)
        print(f"* Fetch {len(rows)} new records.")

        # 如果达到查询上限，为了防止数据丢失，丢弃本次查询结果并降低delta重新查询
        if len(rows) == RESULT_UPPER_LIMIT:
            print(f"返回结果达到上限 {RESULT_UPPER_LIMIT} 条，自动调低 delta 重试")
            delta = timedelta(seconds=delta.seconds / 2)
            start_search_time = end_search_time - delta
            continue

        # 从新获取到的内容里去重，线性时间复杂度，然后添加到全部记录结果`results`里
        cut_index = utils.compare_rows(results, rows)
        print(f"* Add {len(rows) - cut_index} new records.")
        results.extend(rows[cut_index: ])

        # Break 条件
        if end_search_time == start_search_time:
            print(f"* Done. Fetched {len(results)} records")
            break

        # 更新查询时间到下一时间段
        end_search_time = start_search_time
        start_search_time = max(end_search_time - delta, start_time)

    # 保存 Excel 文件到`./results`目录下，默认文件名为时间区间，精确到秒
    utils.save_xlsx(
        header=proc.parseHeader(proc.last_dom),
        rows=results,
        filename=save_filename,
        split_size=split_size
    )

def __main__():
    # 从参数中提取`"--start"`和`"--end"`时间参数
    parser = argparse.ArgumentParser()

    parser.add_argument("--start", type=str, required=False, help='e.g., "20201201-103000"')
    parser.add_argument("--end", type=str, required=False, help='e.g., "20201201-235959"')
    parser.add_argument("--equipments", type=str, default="A", help='e.g., "ABGH"')
    parser.add_argument("--delta_hours", type=int, default=4, help='e.g., 4')
    parser.add_argument("--save", type=str, default='', help='Save filename')
    parser.add_argument("--split_size", type=int, default=100000, help="Limit saving records in single xlsx.")

    args = parser.parse_args()
    start = dateParser(args.start) if args.start else None
    end = dateParser(args.end) if args.end else None
    equipments = args.equipments
    delta_hours = timedelta(hours=args.delta_hours)
    save_name = args.save or None
    split_size = args.split_size

    # 开始循环
    proc = Processor()
    main_loop(proc, start, end, equipments, delta_hours, save_name, split_size)

if __name__ == "__main__":
    __main__()

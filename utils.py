'''一些辅助函数
'''
from pathlib import Path
from datetime import datetime
from dateutil.parser import parse as dateParser
import xlsxwriter


def datetime2Str(t: datetime, pattern="%Y-%m-%d %H:%M:%S"):
    return t.strftime(pattern)


def compare_rows(large: list, small: list):
    '''比较新查询到的结果中，哪部分已经被重复查询过了
    '''
    # [12.15], [12.15], ..., [12.14], [12.14]
    # [12.14], [12.13], ..., [12.13], [12.13]

    if len(large) == 0 or len(small) == 0:
        return 0

    last_item = large[-1]
    last_datetime = dateParser(last_item[0])

    index = 0
    while index < len(small):
        new_item = small[index]
        new_datetime = dateParser(new_item[0])

        #    12.13            12.14
        if new_datetime < last_datetime:
            return index

        if all(new_item[i] == last_item[i] for i in range(len(last_item))):
            return index + 1

        index += 1

    return index


SAVE_DIR = "./results"

def save_xlsx(header, rows, filename="output"):
    '''保存到 Excel 文件中
    '''
    save_dir_path = Path(SAVE_DIR)
    save_dir_path.mkdir(exist_ok=True)

    filename = str(save_dir_path.joinpath(filename))
    workbook = xlsxwriter.Workbook(filename)

    sheet = workbook.add_worksheet()
    header_format = workbook.add_format()
    header_format.set_bold(True)
    header_format.set_align("center")

    order, golden_order = get_order(header)
    convert_time_column(rows, order, golden_order)

    for col, golden_order in enumerate(golden_order):
        sheet.write(0, col, golden_order[1], header_format)

    for row, record in enumerate(rows):
        for col, index in enumerate(order):
            sheet.write(row + 1, col, record[index])

    workbook.close()


def get_order(header: list):
    '''按照正确的顺序重排表头顺序
    '''
    golden_order = [
        ("CenterName", "监控中心"),
        ("GroupName", "行政区划"),
        ("StationName", "局站"),
        ("EquipmentCategory", "设备分类"),
        ("EquipmentName", "设备名"),
        ("SignalName", "信号名"),
        ("SignalValue", "信号值"),
        ("RecordTime", "记录时间"),
        ("Meanings", "信号含义"),
        ("ThresholdType", "存盘方式"),
    ]
    order = [-1 for _ in golden_order]
    for index, (key, _) in enumerate(golden_order):
        order[index] = header.index(key)
        assert order[index] >= 0, f"{key} not exist in {header}"
    return order, golden_order


def convert_time_column(rows, order, golden_order):
    '''把时间列刷成对应的格式
    '''
    time_columns_index = -1
    for golden_index, (key, _) in enumerate(golden_order):
        if key == "RecordTime":
            time_columns_index = order[golden_index]
    assert 0 <= time_columns_index < len(golden_order)
    for row in rows:
        dt = dateParser(row[time_columns_index])
        row[time_columns_index] = datetime2Str(dt, "%Y/%m/%d %H:%M:%S")
    return time_columns_index

# 这两个字段返回了，但是不在结果里显示，不知道干啥的
DEPRECATED_COLUMNS = [
    "BaseTypeName",
    "GroupLineID",
]

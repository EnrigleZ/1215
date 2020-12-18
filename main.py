import argparse
from datetime import datetime
from xml.dom.minidom import Element, Document
from dateutil.parser import parse as dateParser

from processor import Processor
import utils

def main_loop(proc: Processor, startTime: datetime = None, endTime: datetime = None):
    if endTime is None:
        if startTime is None:
            startTime = datetime.now().replace(hour=0, minute=0, second=0)
        endTime = startTime.replace(hour=23, minute=59, second=59)
    proc.updateField("StartTime", utils.datetime2Str(startTime))
    proc.updateField("EndTime", utils.datetime2Str(endTime))

    results = []
    while True:
        print(proc.getField("StartTime"), "---", proc.getField("EndTime"))
        dom = proc.fetch()
        rows = proc.parseRows(dom)

        cut_index = utils.compare_rows(results, rows)
        # print(f"Trimmed {cut_index} duplicated from {len(rows)} new records")
        if cut_index == len(rows):
            print(f"* Done. Fetched {len(results)} records")
            break

        print(f"* Add {len(rows) - cut_index} new records.")
        results.extend(rows[cut_index: ])

        last_datetime = proc.parseLastDateTime(dom)
        new_endtime_str = utils.datetime2Str(last_datetime)
        proc.updateField("EndTime", new_endtime_str)

    pattern = "%Y%m%d-%H%M%S"
    str_start = utils.datetime2Str(startTime, pattern)
    str_end = utils.datetime2Str(endTime, pattern)

    save_filename = f"{str_start}__{str_end}"
    save_filename += ".xlsx"

    print(save_filename)
    utils.save_xlsx(
        header=proc.parseHeader(proc._last_dom),
        rows=results,
        filename=save_filename
    )

def __main__():
    parser = argparse.ArgumentParser()

    parser.add_argument("--start", type=str, required=False, help='e.g., "20201201-103000"')
    parser.add_argument("--end", type=str, required=False, help='e.g., "20201201-235959"')


    args = parser.parse_args()
    start = dateParser(args.start) if args.start else None
    end = dateParser(args.end) if args.end else None

    proc = Processor()
    main_loop(proc, start, end)

if __name__ == "__main__":
    __main__()

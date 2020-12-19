# 一个Project

## 调用方式

```bash
python ./main --start <开始日期+时间> --end <结束日期+时间> --equipments <查询设备>
```

## 参数说明

- `--start`: 开始时间，格式为 `"YYYYMMDD-hhssmm"`，例如 `"20201215-000000"`。时分秒可省略，默认为`-000000`。
- `--end`: 结束时间，格式为 `"YYYYMMDD-hhssmm"`，例如 `"20201215-235959"`。时分秒可省略，默认为`-000000`。

  - 当 `start` 和 `end` 均为空，则设置为查询今日结果。
  - 仅 `end` 为空，则设置为查询从 `start` 到今日结束 `"235959"` 的结果。
  - 仅 `start` 为空，会报错。

- `--equipments`: 查询设备， 支持 `"ABGH"`，例如 `"AB"` 代表仅查询AB两台设备。

## 调用示例

```basg
python ./main.py --start 20201219
```

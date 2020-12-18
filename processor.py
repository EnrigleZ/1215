import os
import requests
from datetime import datetime
from xml.dom.minidom import parseString, Document, Element
from dateutil.parser import parse as dateParser

class Processor:
    '''把网络请求以及结果解析等功能封装到这里了
    '''
    def __init__(self):
        # Request 文本，包含了要查询的参数，四号楼什么的
        self.payload = None
        # 原始的 XML 结构化参数
        self.payload_xml = None

        # 从文件里读初始参数，并且初始化当前本地查询时间
        with open("configs/params.xml", "r", encoding="utf-8") as file:
            self.payload = file.read()
            self.payload_xml = parseString(self.payload)
            self.updateQueryTime()

        # 请求头，反正不加这几行的话，后端就报错
        self.headers = {
            'Content-Type': 'text/xml; charset=utf-8',
            'Cookie': 'ASP.NET_SessionId=q4bcmh4x4phxepga5mlrkfke; Token=b4d4ae9f-1aca-401b-ab00-318904d6f4df; User_Id=admin; CurrentUserId=-1',
            'SOAPAction': '"http://tempuri.org/IQueryReportService/Query"'
        }

        # cache 最后一次获取的 Response 内容
        self.last_dom = None

    @property
    def url(self):
        '''API Link
        '''
        return "http://10.184.17.9/ReportService/QueryReportService.svc"

    @classmethod
    def parseHeader(cls, dom: Document):
        '''从返回的结果中解析表头部分
        '''
        header = dom.getElementsByTagName("xs:sequence")[0]
        header_nodes = header.getElementsByTagName("xs:element")
        colnames = [node.getAttribute("name") for node in header_nodes]
        return colnames

    @classmethod
    def parseRows(cls, dom: Document):
        '''从返回的结果中解析每一行，用列表的形式表示每一行的八个字段
        '''
        ret = []
        headers = cls.parseHeader(dom)

        table_nodes = dom.getElementsByTagName("Table")
        for table_node in table_nodes:
            row = []
            for colname in headers:
                value_nodes = table_node.getElementsByTagName(colname)
                value = '' if len(value_nodes) == 0\
                    else value_nodes[0].childNodes[0].nodeValue
                row.append(value)
            ret.append(row)

        return ret

    @classmethod
    def parseLastDateTime(cls, dom: Document, timeField: str = "RecordTime"):
        '''从返回的全部记录里，找到最后一条记录的对应时间，用来更新下次查询的结束时间
        '''
        table_nodes = dom.getElementsByTagName("Table")
        if len(table_nodes) == 0:
            return None

        last_table_node: Element = table_nodes[-1]
        date_str = last_table_node.getElementsByTagName(timeField)[0].childNodes[0].nodeValue
        date_obj = dateParser(date_str)

        return date_obj


    def fetch(self):
        '''发送一次查询 Request
        '''
        # Update payload here?
        payload = self.payload.encode('utf-8')

        response = requests.request(
            "POST",
            self.url,
            headers=self.headers,
            data=payload
        )

        dom = parseString(response.text)
        self.last_dom = dom
        return dom


    def updatePayload(self):
        '''将 Request 查询字段内容更新成 XML 里的参数
        '''
        self.payload = self.payload_xml.toxml()


    def updateField(self, fieldName: str, value: str):
        '''更新请求查询字段里的某个值，比如更新查询结束时间
        '''
        fieldname_nodes = self.payload_xml.getElementsByTagName("tns:Name")
        for node in fieldname_nodes:
            if len(node.childNodes) == 0:
                continue
            if node.childNodes[0].nodeValue == fieldName:
                value_node: Element = node.parentNode.getElementsByTagName("tns:Value")[0]
                if value_node:
                    value_node.firstChild.replaceWholeText(value)
        self.updatePayload()


    def getField(self, fieldName: str):
        '''获取请求查询字段里的某个值
        '''
        fieldname_nodes = self.payload_xml.getElementsByTagName("tns:Name")
        for node in fieldname_nodes:
            if len(node.childNodes) == 0:
                continue
            if node.childNodes[0].nodeValue == fieldName:
                value_node: Element = node.parentNode.getElementsByTagName("tns:Value")[0]
                if value_node:
                    return value_node.firstChild.nodeValue
        return 'not found'

    def updateQueryTime(self):
        '''更新发送请求的当前时间
        '''
        query_time_node = self.payload_xml.getElementsByTagName("tns:queryTime")[0]
        current_time = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        query_time_node.firstChild.replaceWholeText(current_time)

        self.updatePayload()

    def testSaveXML(self, dom=None, name=None):
        '''没用，Debug 的
        '''
        name = name if name is not None else "output.xml"
        dom = dom if dom else self.last_dom

        print(dom.toprettyxml(newl='', indent=''), file=open(name, "w", encoding="utf-8"))


    def testSaveRows(self, dom=None, name=None):
        '''没用，Debug 的
        '''
        name = name if name is not None else "output.csv"
        dom = dom if dom else self.last_dom

        header = self.parseHeader(dom)
        rows = self.parseRows(dom)
        ncols = len(header)

        assert all(len(row) == ncols for row in rows)

        with open(name, "w", encoding="utf-8") as file:
            file.write(", ".join(header) + "\n")

            for row in rows:
                file.write(", ".join(row) + "\n")
        print(f"* Save files to {name}.")


def fun():
    '''没用，Debug 的
    '''
    proc = Processor()
    dom = proc.fetch()
    ret = proc.parseRows(dom)
    return proc, ret
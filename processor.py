import os
import requests
from datetime import datetime
from xml.dom.minidom import parseString, Document, Element
from dateutil.parser import parse as dateParser

class Processor:
    def __init__(self):
        self.payload = None
        self.payload_xml = None
        with open("configs/params.xml", "r", encoding="utf-8") as file:
            self.payload = file.read()
            self.payload_xml = parseString(self.payload)
            self.updateQueryTime()

        self.headers = {
            'Content-Type': 'text/xml; charset=utf-8',
            'Cookie': 'ASP.NET_SessionId=q4bcmh4x4phxepga5mlrkfke; Token=b4d4ae9f-1aca-401b-ab00-318904d6f4df; User_Id=admin; CurrentUserId=-1',
            'SOAPAction': '"http://tempuri.org/IQueryReportService/Query"'
        }

        self._last_dom = None

    @property
    def url(self):
        return "http://10.184.17.9/ReportService/QueryReportService.svc"

    @classmethod
    def parseHeader(cls, dom: Document):
        header = dom.getElementsByTagName("xs:sequence")[0]
        header_nodes = header.getElementsByTagName("xs:element")
        colnames = [node.getAttribute("name") for node in header_nodes]
        return colnames

    @classmethod
    def parseRows(cls, dom: Document):
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
        table_nodes = dom.getElementsByTagName("Table")
        if len(table_nodes) == 0:
            return None

        last_table_node: Element = table_nodes[-1]
        date_str = last_table_node.getElementsByTagName(timeField)[0].childNodes[0].nodeValue
        date_obj = dateParser(date_str)

        return date_obj


    def fetch(self):
        # Update payload here?
        payload = self.payload.encode('utf-8')

        response = requests.request(
            "POST",
            self.url,
            headers=self.headers,
            data=payload
        )

        dom = parseString(response.text)
        self._last_dom = dom
        return dom


    def updatePayload(self):
        self.payload = self.payload_xml.toxml()


    def updateField(self, fieldName: str, value: str):
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
        query_time_node = self.payload_xml.getElementsByTagName("tns:queryTime")[0]
        current_time = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        query_time_node.firstChild.replaceWholeText(current_time)

        self.updatePayload()

    def saveAsExcel(self, results: list):
        pass

    def testSaveXML(self, dom=None, name=None):
        name = name if name is not None else "output.xml"
        dom = dom if dom else self._last_dom

        print(dom.toprettyxml(newl='', indent=''), file=open(name, "w", encoding="utf-8"))


    def testSaveRows(self, dom=None, name=None):
        name = name if name is not None else "output.csv"
        dom = dom if dom else self._last_dom

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
    proc = Processor()
    dom = proc.fetch()
    ret = proc.parseRows(dom)
    return proc, ret
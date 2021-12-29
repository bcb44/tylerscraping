from bs4.element import Tag

class Provider(object):
    def __init__(self, name:str=None, degree:str=None, email:str=None, addr:str=None, loc:str=None, site:str=None):
        self.name = name
        self.degree = degree
        self.email = email
        self.addr = addr
        self.loc = loc
        self.site = site

    def __str__(self) -> str:
        result = _qt(self.name)
        result += f',{_qt(self.degree)}'
        result += f',{_qt(self.loc)}'
        result += f',{_qt(self.email)}'
        result += f',{_qt(self.addr)}'
        result += f',{_qt(self.site)}'
        return result
        

def _qt(value:str):
    if value is None: return ''
    if ',' in value:
        value = f'"{value}"'
    return value

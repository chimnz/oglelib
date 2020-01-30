from io import StringIO
import numpy as np

class PhotParser(object):
    '''For parsing phot.dat files. Takes contents of file as arg.'''
    def __init__(self, filecontents):
        self.contents = filecontents

    def getdata(self):
        data = {}
        fileobj = StringIO(self.contents)
        data['t'], data['I'], data['Ierr'] = np.loadtxt(fileobj, usecols=(0,1,2), unpack=True)
        return data

class ParamsParser(object):
    '''For parsing params.dat files. Takes contents of file as arg.'''
    def __init__(self, filecontents):
        self.contents = filecontents

    def __get_rows(self):
        rows = self.contents.split('\n')
        return rows

    def __parse_top_rows(self, rows):
        p = {}
        toprows = rows[2:6+1]  # top 5 lines
        # split these lines by whitespace, once (name, value)
        toprows = [r.split(maxsplit=1) for r in toprows]

        for r in toprows[:4]:
            name = r[0]
            val = r[-1]
            p.update({name: val})
        p.update({'Remarks': ''})

        # rename RA and Dec dict keys
        p['RA'] = p.pop('RA(J2000.0)')
        p['Dec'] = p.pop('Dec(J2000.0)')

        lastrow = toprows[-1]
        if len(lastrow) > 1:  # there are remarks
            p.update({lastrow[0]: lastrow[1]})  # entry: {Remarks: s}
        return p

    def __parse_bottom_rows(self, rows):
        p = {}
        bottomrows = rows[8:]  # bottom 8 params
        # split rows by whitespace, returns (name, value, error) list
        bottomrows = [r.split() for r in bottomrows]

        for r in bottomrows:
            name = r[0]
            val, err = r[1], r[2]
            if (val is '-') or (err is '-'):
                val, err = None, None
            else:
                val, err = float(val), float(err)
            p.update({name: val, name+'_err': err})
        return p

    def get_params(self):
        params = {}
        rows = self.__get_rows()

        top = self.__parse_top_rows(rows)
        bottom8 = self.__parse_bottom_rows(rows)

        params.update(top), params.update(bottom8)
        return params

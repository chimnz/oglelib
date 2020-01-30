from string import Template
from ftplib import FTP, error_perm, error_temp
from io import StringIO
import os, sys

ftp_url = 'ftp.astrouw.edu.pl'

filepath_temp = Template(
    '/ogle/ogle${version_num}/ews/${year}/'
    '${field}-${n}/${dat_type}.dat'
)

local_filepath_temp = Template(
    '${datadir}/${year}/${field}-${padded_n}/${dat_type}.dat'
)

def get_ogle_version(year):
    '''Determine ogle version (2,3,4) from given year.'''
    if 1998 <= year <= 2000:
        version = 2
    elif 2002 <= year <= 2009:
        version = 3
    elif 2011 <= year <= 2019:
        version = 4
    else:
        raise Exception('Unsupported year.')
    return(version)

def padded_n(n, year):
    '''Pad the event number, n, with appropriate number of leading zeros.'''
    version = get_ogle_version(year)
    if version == 4:  # ogle4
        nwidth = 4
    elif version == 3:  # ogle3
        nwidth = 3
    elif version == 2:  # ogle2
        nwidth = 2
    n = str(n).zfill(nwidth)  # convert to string, add leading zeroes if necessary
    return(n)


class DatStream(StringIO):
    '''Modified StringIO object whose write method appends
    a newline to the stream.'''
    def __init__(self):
        super().__init__()
    def write(self, s):
        '''Additional newline appended makes this method suitable for
        usage as a callback function for ftplib.FTP.retrlines method
        since newlines are automatically stripped from the output to be
        appended to the stream/file.'''
        super().write(s + '\n')
    def getvalue(self):
        v = super().getvalue().strip()
        return(v)


class RemoteDatFile(object):
    '''Represent datfile that is not present on local filesystem.'''
    def __init__(self, year, n, field, dat_type):
        self.year = year
        self.n = padded_n(n, year)
        self.field = field

        self.dat_type = dat_type  # phot/params

        self.filepath = self.__ftp_filepath()
        self.fileurl = self.__ftp_fileurl(self.filepath)

    def __ftp_filepath(self):
        '''Return filepath filepath relative to root director (/)
        on ogle ftp server.'''
        version_num = get_ogle_version(self.year)
        filepath = filepath_temp.substitute(
            version_num=version_num, year=self.year,
            n=self.n, dat_type=self.dat_type,
            field=self.field
        )
        return(filepath)

    def __ftp_fileurl(self, filepath):
        '''Return ftp file url that can be pasted into browser
        search bar for easy access to specific file.'''
        fileurl = 'ftp://' + ftp_url + self.filepath
        return(fileurl)

    def get_contents(self, ftp):
        '''Retrieve contents of dat file with given
        dat_type (phot, params). Takes ftplib.FTP object as argument.'''
        cmd = 'RETR {}'.format(self.filepath)

        with DatStream() as stream:
            try:
                ftp.retrlines(cmd, stream.write)
                filecontents = stream.getvalue()
            except error_perm as e:
                err_msg = str(e)
                err_code = int(err_msg.split()[0])
                if err_code == 550:
                    msg = 'url: {} is invalid'.format(self.filepath)
                elif err_code == 530:
                    msg = 'ftp is not enabled'
                raise Exception(msg)
            except (error_temp, BrokenPipeError) as e:  # connection was idle for too long resulting in timeout or broken pipe error
                # reload ftp client
                ftp.close()
                ftp.connect(ftp_url)
                ftp.login()
                # try again
                self.get_contents(ftp)
        return(filecontents)


class DatFile(object):
    def __init__(self, fileurl, filecontents):
        self.fileurl = fileurl
        self.contents = filecontents.strip()


class FileGrabber(object):
    '''Object whose purpose is retrieving datfiles. Search for files
    on local filesystem before attempting to download files from
    ogle ftp server. Default data search directory must be specified as datadir
    or else uses environment variable OGLEDATADIR as default search path.'''
    def __init__(self, datadir=None, ftp_enabled=False):
        self.datadir = self.__verify_datadir(datadir)
        if ftp_enabled:
            self.ftpclient = FTP(ftp_url)
            self.ftpclient.login()

    def __verify_datadir(self, datadir):
        '''Make sure datadir exists, and format its path properly.'''
        if datadir is None:
            if 'OGLEDATADIR' in os.environ:
                datadir = os.environ['OGLEDATADIR']
            else:
                pass
        else:
            if os.path.isdir(datadir):  # make sure data directory exists
                if datadir.endswith('/'):  # remove trailing "/"
                    datadir = datadir[-1]
            else:
                msg = 'Invalid data directory.'
                raise Exception(msg)
        return(datadir)

    def __get_local_filepath(self, year, n, field, dat_type):
        '''Return local filepath of [dat_type(phot/params)].dat file
        with specified year, n, field.'''
        local_filepath = local_filepath_temp.substitute(
            datadir=self.datadir, year=year, field=field.lower(),
            padded_n=padded_n(n, year), dat_type=dat_type
        )
        return(local_filepath)

    def get_datfile(self, year, n, field, dat_type):
        '''Return filegrabber.Datfile object with specified year, n, field,
        and dat_type. Search specified datadir before attempting to retrieve
        datfile contents from ogle ftp server.'''
        rdf = RemoteDatFile(year, n, field, dat_type)

        if self.datadir is not None:  # data directory provided
            local_filepath = self.__get_local_filepath(year, n, field, dat_type)
            if os.path.isfile(local_filepath):  # file already downloaded, use this file
                with open(local_filepath, 'r') as f:
                    contents = f.read()
            else:  # file not yet downloaded, download file
                contents = rdf.get_contents(self.ftpclient)
        else:  # no data directory provided, download file
            contents = rdf.get_contents(self.ftpclient)
        datfile = DatFile(rdf.fileurl, contents)
        return(datfile)

    def __force_write(self, filepath, s):
        '''Write string [s] to filepath [filepath] no matter what.'''
        if os.path.isfile(filepath):
            pass  # file already exists, do nothing
            return(0)  # nothing was written
        else:  # file does not exist
            event_dir = os.path.dirname(filepath)  # format: [field]-[padded_n]
            if not os.path.exists(event_dir):  # if event_dir does not exist
                os.makedirs(event_dir, exist_ok=True)  # create necessary dirs
            else:
                pass  # event_dir already exists, do not create dirs
            with open(filepath, 'w') as f:
                f.write(s)
            return(1)  # file was successfully written

    def save(self, year, n, field='blg'):
        '''Download and save phot.dat and params.dat file for specfied
        year, n, field in datadir with which the class was instantiated.'''
        if self.datadir is not None:
            dat_types = ('phot', 'params')
            for dt in dat_types:
                datfile = self.get_datfile(year, n, field, dt)
                filepath = self.__get_local_filepath(year, n, field, dt)
                outcome = self.__force_write(filepath, datfile.contents)
                if outcome == 0:
                    print('{0} {1}'.format(filepath, 'exists'))
                elif outcome == 1:
                    print('{0} {1}'.format(filepath, 'saved'))
        else:
            msg = 'No data directory provided.'
            raise Exception(msg)

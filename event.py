from oglelib.filegrabber import padded_n, FileGrabber
from oglelib.parse import PhotParser, ParamsParser
from oglelib.calculations import Lightcurve, reduced_chi_square, ra, dec, pgram
import matplotlib.pyplot as plt
import numpy as np
from os import environ

plt.rcParams.update({'figure.max_open_warning': 0})  # suppress too many open figures warning

class Event(object):
    def __init__(self, year, n, field='blg', fgrabber=None, sigmamin=0.0):
        '''Return ogle Event object for specified year (yyyy), event number
        (1,2,3...), and field (BLG, LMC, SMC). If no fgrabber is specified, 
        will create filegrabber object using datadir specified in OGLEDATADIR
        environment variable.'''
        self.year = year
        self.n = n
        self.field = field.lower()

        self.title = '{}-{}-{}'.format(
            self.year, self.field.upper(), padded_n(self.n, self.year)
        )

        if fgrabber == None:
            if 'OGLEDATADIR' in environ:
                defaultpath = environ['OGLEDATADIR']
            else:
                defaultpath = None
            fgrabber = FileGrabber(defaultpath)

        self.phot_datfile = fgrabber.get_datfile(year, n, field, 'phot')
        self.params_datfile = fgrabber.get_datfile(year, n, field, 'params')

        self.params = self.__params()

        if field is 'blg':
            self.lightcurve = Lightcurve(self.params)

        self.sigmamin = sigmamin  # sigma_min for Ierr correction

    def __params(self):
        '''Return dictionairy of paramters from params.dat file.'''
        params_parser = ParamsParser(self.params_datfile.contents)
        params = params_parser.get_params()
        # convert RA and Dec to degrees
        params.update({
            'RA': ra(params['RA']), 'Dec': dec(params['Dec'])
        })
        return params

    def data(self, cleanse=True):
        '''Return data as dict with keys t, I, and Ierr.'''
        phot_parser = PhotParser(self.phot_datfile.contents)
        t, I, Ierr = phot_parser.getdata().values()

        if cleanse:
            ## remove placeholder values
            ind = np.where(I < 25)
            t = t[ind]
            I = I[ind]
            Ierr = Ierr[ind]
            ## implement Ierr quadrature correction
            Ierr = np.sqrt(Ierr**2 + self.sigmamin**2)  # Ierr_tot

        return t, I, Ierr

    def datapoints(self):
        '''Return data as one dimensional list of tuples containing
        (t, I, Ierr).'''
        t, I, Ierr = self.data()
        dp = [( t[i], I[i], Ierr[i] ) for i in range(len(t))]
        return dp

    def rcs(self, degfreedom=5):
        '''Calculate reduced chi square value of event data. The self.sigmamin is
        the sigma_min value used in the sigma_i_tot correction. The degfreedom
        represents the number of degrees of freedom (Ibl, umin, tE, t0, fbl).'''
        lc = self.lightcurve
        mag_func = lc.mag  # function for computing magnitude

        datapoints = self.datapoints()  # t, I, Ierr
        rcs = reduced_chi_square(datapoints, mag_func, Nu=degfreedom)
        return rcs

    def plot(self, halfwidth_scale=2, toffset=2450000, xlims='auto', **kwargs):
        '''Take matplot.pyplot object as arg and perform graphing operations
        using this the provided object. The halfwidth is calculated as [halfwidth_scale] * tE.'''
        lc = self.lightcurve

        # create figure
        fig = plt.figure(**kwargs)
        axes = fig.add_subplot(1,1,1)  # first two args are grid dimensions and last arg is location number

        # prepare data
        tdata, Idata, Ierrdata = self.data()

        # prepare model
        model = lc.centered_vals(tdata)
        tmodel = model['t']
        Imodel = model['I']

        # subtract toffset from t values for easier comprehension
        tdata = [t-toffset for t in tdata]
        tmodel = [t-toffset for t in tmodel]

        # plot data
        axes.errorbar(tdata, Idata, yerr=Ierrdata, fmt='.')
        # plot model
        axes.plot(tmodel, Imodel)

        # format chart
        axes.set_xlabel('HJD - {}'.format(toffset), fontsize=12)  # days
        axes.set_ylabel('I-band magnitude', fontsize=12)
        plot_title = self.title
        axes.set_title(plot_title, fontsize=12)

        # set x-axis limits
        xmin = xmax = None
        if xlims == 'auto':  # xlims automatically chosen by matplotlib
            pass
        elif xlims == 'peak':  # center xlims around Tmax
            tE = self.params['tau']
            t0 = self.params['Tmax'] - toffset
            halfwidth = halfwidth_scale * tE
            xmin = t0 - halfwidth
            xmax = t0 + halfwidth
        axes.set_xlim(xmin, xmax)


        # return figure with inverted plot
        fig.gca().invert_yaxis()
        return(fig)

    def pgram(self):
        tdata, Idata = self.data()[:2]
        pgramdict = pgram(tdata, Idata)
        return pgramdict

    def pgramplot(self, **kwargs):
        pgram = self.pgram()
        fig = plt.figure()

        axes = fig.add_subplot(1,1,1)  # first two args are grid dimensions and last arg is location number
        axes.plot(pgram['freq'], pgram['pgram'])

        axes.set_xlabel('freq')
        axes.set_ylabel('pgram')
        axes.set_title(self.title)
        return fig







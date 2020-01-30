import numpy as np
from math import sqrt, log10, floor
import scipy.signal as signal


class Lightcurve(object):
    def __init__(self, params):
        self.Ibl = params['I_bl']  # incident magnitude
        self.umin = params['umin']  # impact parameter
        self.tE = params['tau']  # characteristic timescale
        self.t0 = params['Tmax']  # time of max intensity
        self.fbl = self.__validate_fbl(params['fbl'])  # blending fraction

    def __validate_fbl(self, fbl):
        if fbl > 1:
            fbl = 1
        elif fbl < 0:
            fbl = 0
        return fbl

    def mag(self, t):
        '''Compute magnitude of lens with respect to time.'''
        u = sqrt(
            self.umin**2 + ( (t-self.t0) / self.tE )**2
        )
        flux_ratio = ((u**2 + 2)/(u * sqrt(u**2 + 4)))
        # consider blending fraction
        flux_ratio = (flux_ratio-1) * self.fbl + 1
        mag = -2.5 * log10(flux_ratio) + self.Ibl
        return mag  # I

    def centered_vals(self, time_array):
        '''Generate lightcurve centered around the time of max
        intensity t_0. Return list with value format (t, I).'''
        first_t = floor(min(time_array))
        last_t = floor(max(time_array))
        tmodel = np.arange(first_t, last_t+1, 1/24)
        Imodel = np.array([self.mag(t) for t in tmodel])
        model = {'t':tmodel, 'I':Imodel}
        return model

def ra(timestring):
    hr, mins, sec = [float(s) for s in timestring.split(':')]
    ans = 15 * (hr + (mins/60) + (sec/3600))
    return round(ans, 3)

def dec(timestring):
    hr, mins, sec = [float(s) for s in timestring.split(':')]
    ans = hr + (mins/60) + (sec/3600)
    return round(ans, 3) 

def pgram(tdata, Idata):
    crop = False  # cropping for Fourier transform
    if crop:
        ind = np.where(tdata > 2453000)
        tdata = tdata[ind]
        Idata = Idata[ind]

    # more steps
    tdata = tdata-2450000
    freq = np.linspace(0.0001, 0.03, 10000)  # angular
    pgram = signal.lombscargle(tdata, Idata, freq, normalize=True)  # ???

    pgramtemp = pgram[np.where(freq > 0.01)]

    maxpgram = np.max(pgramtemp)  # ???
    freq_at_maxgram = freq[np.where(np.max(pgram) == pgram)][0]  # angular frequency at maxpgram
    parallax_period = 2 * np.pi / freq_at_maxgram
    maxpgram365 = np.mean(pgram[np.where(np.abs(freq - 0.017) < 0.00001)])
    maxpgram365_norm = maxpgram365 / maxpgram

    def getfwhm():
        # Full width half max:
        i=np.where(pgram==maxpgram)[0][0]
        j=i
        lowflag = highflag = 0
        lower = higher = 0
        while j > 0 and i < len(pgram)-1:
            if pgram[j] >= maxpgram/2 and pgram[j-1] < maxpgram/2 and lowflag==0 :
                lower=freq[j-1]
                lowflag=1
            if pgram[i] >= maxpgram/2 and pgram[i+1] < maxpgram/2 and highflag==0 :
                higher=freq[i+1]
                highflag=1
            if lowflag==1 and highflag==1 :
                break
            i=i+1
            j=j-1
        if highflag==0 or lowflag==0:
            fwhm = 0.0
        else:
            fwhm = higher - lower
        return fwhm
    fwhm = getfwhm()

    return {
        'maxpgram': round(maxpgram, 4),
        'freq_at_maxpgram': round(freq_at_maxgram, 6),
        'parallax_period': round(parallax_period, 4),
        'maxpgram365': round(maxpgram365, 4),
        'maxpgram365_norm': round(maxpgram365_norm, 8),
        'fwhm': round(fwhm, 6),
        'freq': freq,
        'pgram': pgram,
    }

def reduced_chi_square(datapoints, func, Nu):
    '''Calculate reduced chi-square using provided datapoints
    ( as list with value format: (t,I,Ierr) ), function for obtaining
    calculated values, the number of fitted parameters (degrees of freedom) Nu.'''
    # calculated using formula from wikipedia:
    # https://en.wikipedia.org/wiki/Reduced_chi-squared_statistic
    thesum = 0
    for i in range(len(datapoints)):
        dp = datapoints[i]  # (x, y, yerr) ==> (t, I, Ierr)

        Oi = dp[1]  # I (data)
        sigma_i = dp[2]  # Ierr (data)

        x = dp[0]  # t (data)
        Ci = func(x)  # I (model)

        square_diff = (Oi - Ci)**2
        variance = sigma_i**2

        addend = square_diff / variance
        thesum += addend
    rcs = thesum / ( len(datapoints) - Nu )
    return round(rcs, 3)

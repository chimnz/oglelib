# oglelib
A library for downloading and interacting with data from the
ogle early warning system ([ews](http://ogle.astrouw.edu.pl/ogle4/ews/ews.html)).

# dependencies
install these with pip3 before attempting to use this library:
* numpy
* matplotlib

# tutorial

terms:
* `saved` data refers to data that is on the local filesystem in the specified data directory
* `downloaded` data refers to data that is retrieved from the ogle ftp server without necessarily being saved

*After cloning this repository and either placing "oglelib" into your working
directory or adding "microlensing" to your
[`PYTHONPATH`](https://docs.python.org/3/using/cmdline.html#envvar-PYTHONPATH), you should be able to import individual classes from oglelib as I've shown below.*


####  1. Saving event data using FileGrabber class
```python
from oglelib.filegrabber import FileGrabber

# specify directory in which to save the data
path = '/Users/chris/Desktop/ogle_datadir'
# ftp must be enabled so that files can be pulled from ftp server
fg = FileGrabber(datadir=path, ftp_enabled=True)

# downloading data for events 2018-blg-0001 to 2018-blg-0003
for n in range(1, 4):
    fg.save(2018, n)  # "blg" is the default value for the "field" parameter
```

*If the event class is not given an fgrabber argument, it will attempt to create an offline FileGrabber using the path specified in the `OGLEDATADIR` environment variable.*

#### 2. Interacting with downloaded event data using Event class
```python
from oglelib.filegrabber import FileGrabber
from oglelib.event import Event

def example_function(event):
    pass

# specifying the directory in which to search for saved data
# this directory only contains data for 2018-blg-0001:0003
path = '/Users/chris/Desktop/ogle_datadir'
# ftp is not enabled since we do not intend to download any additional data
fg = FileGrabber(datadir=path)  # ftp_enabled == False by default

for n in range(1,4):  # 1,2,3
    e = Event(2018, n, fgrabber=fg)   # "blg" is default value for "field"

    event_params = e.params  # return dict whose keys match the parameter names
                             # in the "params.dat" file with keys for error values
                             # given as "{parameter_name}_err"
    print(event_params["Dmag"])  # print Dmag for this event
    print(event_params["Dmag_err"])  # print error in Dmag for this event

    reduced_chi_square = e.rcs()  # return reduced chi square value as float
    if reduced_chi_square <= 5:
        example_function(e)
```


#### 3. Accessing event data that is not present in your specified local data directory
```python
from oglelib.filegrabber import FileGrabber
from oglelib.event import Event

# this directory only contains data for 2018-blg-0001:0003
path = '/Users/chris/Desktop/ogle_datadir'

# enable ftp and do not supply datadir
fg = FileGrabber(ftp_enabled=True)
for n in range(7,10):  # 7,8,9
    e = Event(2018, n, fgrabber=fg)
    data = e.data()  # return dict with keys (t, I, Ierr) each being a
                     # list of values for each physical quantity, respectively

    print(min(data["I"]))  # can determine min intensity value for each event
```


#### 4. Interacting with saved data and downloading (without saving) any missing data from the ftp server
```python
from oglelib.filegrabber import FileGrabber
from oglelib.event import Event

# this directory contains data for 2018-blg-0001:0003 but not for 2018-blg-0004:0006
path = '/Users/chris/Desktop/ogle_datadir'

fg = FileGrabber(datadir=path, ftp_enabled=True)
events = []
for n in range(1,7):  # 1,2,3,4,5,6
    e = Event(2018, n, fgrabber=fg)
    events.append(e)

# can determine which event has lowest reduced chi square value
rcs_vals = [e.rcs() for e in events]
min_rcs = min(rcs_vals)
index_of_min_val = rcs_vals.index(min_rcs)
best_fitting_event = events[index_of_min_val]
````

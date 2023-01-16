import os 
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


########## Checks if path exists, if not then creates directory ##########
def check_path(basepath, path):
    ''' Created by Elliott Abe '''
    if path in basepath.as_posix():
        return basepath
    elif not (basepath / path).exists():
        (basepath / path).mkdir(exist_ok=True,parents=True)
        print('Added Directory:'+ (basepath / path).as_posix())
        return (basepath / path)
    else:
        return (basepath / path)


def discrete_cmap(N, base_cmap=None):
    """Create an N-bin discrete colormap from the specified input map"""

    # Note that if base_cmap is a string or None, you can simply do
    #    return plt.cm.get_cmap(base_cmap, N)
    # The following works for string, None, or a colormap instance:

    base = plt.cm.get_cmap(base_cmap)
    color_list = base(np.linspace(0, 1, N))
    cmap_name = base.name + str(N)
    return base.from_list(cmap_name, color_list, N)

def normimgs(comb,per_frame=False):
    if per_frame:
        comb = (comb - np.min(comb,axis=(-1,-2))[:,np.newaxis,np.newaxis])/(np.max(comb,axis=(-1,-2))-np.min(comb,axis=(-1,-2)))[:,np.newaxis,np.newaxis]
    else:
        comb = (comb - np.min(comb))/(np.max(comb)-np.min(comb))
    
    return (comb*255).astype(np.uint8)

def add_colorbar(mappable,linewidth=2,location='right',**kwargs):
    ''' modified from https://supy.readthedocs.io/en/2021.3.30/_modules/supy/util/_plot.html'''
    from mpl_toolkits.axes_grid1 import make_axes_locatable
    last_axes = plt.gca()
    ax = mappable.axes
    fig = ax.figure
    divider = make_axes_locatable(ax)
    cax = divider.append_axes(location, size="5%", pad=0.1)
    cbar = fig.colorbar(mappable, cax=cax, drawedges=False,**kwargs)
    cbar.outline.set_linewidth(linewidth)
    plt.sca(last_axes)
    return cbar


def sizeof_fmt(num, suffix='B'):
    ''' by Fred Cirera,  https://stackoverflow.com/a/1094933/1870254, modified'''
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f %s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f %s%s" % (num, 'Yi', suffix)



def nan_helper(y):
    """ modified from: https://stackoverflow.com/questions/6518811/interpolate-nan-values-in-a-numpy-array
    Helper to handle indices and logical indices of NaNs.
    Input:
        - y, 1d numpy array with possible NaNs
    Output:
        - nans, logical indices of NaNs
        - index, a function, with signature indices= index(logical_indices),
          to convert logical indices of NaNs to 'equivalent' indices
    Example:
        >>> # linear interpolation of NaNs
        >>> nans, x= nan_helper(y)
        >>> y[nans]= np.interp(x(nans), x(~nans), y[~nans])
    """
    return np.isnan(y), lambda z: z.nonzero()[0]

def interp_nans(y):
    nans, x = nan_helper(y)
    y[nans]= np.interp(x(nans), x(~nans), y[~nans])
    return y

def nanxcorr(x, y, maxlag=25):
    """ Cross correlation ignoring NaNs.
    Parameters:
    x (np.array): array of values
    y (np.array): array of values to shift, must be same length as x
    maxlag (int): number of lags to shift y prior to testing correlation (default 25)
    
    Returns:
    cc_out (np.array): cross correlation
    lags (range): lag vector
    """
    lags = range(-maxlag, maxlag)
    cc = []
    for i in range(0, len(lags)):
        # shift data
        yshift = np.roll(y, lags[i])
        # get index where values are usable in both x and yshift
        use = ~pd.isnull(x + yshift)
        # some restructuring
        x_arr = np.asarray(x, dtype=object)
        yshift_arr = np.asarray(yshift, dtype=object)
        x_use = x_arr[use]
        yshift_use = yshift_arr[use]
        # normalize
        x_use = (x_use - np.mean(x_use)) / (np.std(x_use) * len(x_use))
        yshift_use = (yshift_use - np.mean(yshift_use)) / np.std(yshift_use)
        # get correlation
        cc.append(np.correlate(x_use, yshift_use))
    cc_out = np.hstack(np.stack(cc))

    return cc_out, lags

def str_to_bool(value):
    """ Parse strings to read argparse flag entries in as bool.
    
    Parameters:
    value (str): input value
    
    Returns:
    bool
    """
    if isinstance(value, bool):
        return value
    if value.lower() in {'False', 'false', 'f', '0', 'no', 'n'}:
        return False
    elif value.lower() in {'True', 'true', 't', '1', 'yes', 'y'}:
        return True
    raise ValueError(f'{value} is not a valid boolean value')


def get_freer_gpu():
    os.system('nvidia-smi -q -d Memory |grep -A4 GPU|grep Used >tmp')
    memory_available = [int(x.split()[2]) for x in open('tmp', 'r').readlines()]
    return np.argmin(memory_available)

def h5store(filename, df, **kwargs):
    """_summary_

    Args:
        filename (str): path to h5 file
        df (pd.DataFrame): DataFrame to save
        **kwards (dict): dictionary key/values to save as metadata
    """
    store = pd.HDFStore(filename)
    store.put('mydata', df)
    store.get_storer('mydata').attrs.metadata = kwargs
    store.close()
    
def h5load(filename):
    """ load h5 pandas DataFrame with metadata

    Args:
        filename (str): path to h5 file

    Returns:
        data (pd.DataFrame): DataFrame 
        metadata (dict): dictionary containing metadata
    """
    store = pd.HDFStore(filename)
    data = store['mydata']
    metadata = store.get_storer('mydata').attrs.metadata
    return data, metadata
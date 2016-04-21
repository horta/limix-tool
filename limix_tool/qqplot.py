from __future__ import division, absolute_import
import numpy as np
from scipy.special import betaincinv
from numba import jit
from limix_plot import cycler_ as cycler
from limix_util.dict_ import OrderedDict

@jit
def _rank_confidence_band(nranks):
    alpha = 0.01
    n = nranks

    mean = np.linspace(1./(n+1), n/(n+1.), n, endpoint=True)
    top = np.empty(n)
    bottom = np.empty(n)
    for k in range(1, n+1):
        top[k-1] = betaincinv(k, n + 1 - k, 1-alpha)
        bottom[k-1] = betaincinv(k, n + 1 - k, alpha)

    return (bottom, mean, top)

class QQPlot(object):
    def __init__(self, axes):
        self._axes = axes
        self._pv = OrderedDict()
        self._color = dict()
        self._properties = dict()

    def add(self, pv, label, color=None, props=None):
        self._pv[label] = np.asarray(pv)

        if color:
            self._color[label] = color
        else:
            prop = cycler.next(self._axes)
            if 'color' in prop:
                self._color[label] = prop['color']
            else:
                self._color[label] = None
        self._properties[label] = props

    @property
    def _max_size(self):
        return max([len(v) for v in self._pv.itervalues()])

    def plot(self, confidence=True, plot_top=100, legend=True):
        axes = self._axes
        labels = self._pv.keys()
        for label in labels:
            self._plot_points(label, plot_top)

        if confidence:
            self._plot_confidence_band()

        axes.grid(False)
        axes.tick_params(axis='both', which='major', direction='out')
        axes.spines['right'].set_visible(False)
        axes.spines['top'].set_visible(False)
        axes.yaxis.set_ticks_position('left')
        axes.xaxis.set_ticks_position('bottom')


        N = self._max_size
        axes.set_xlim([0, -np.log10(1/(N+1))])

        if legend:
            self._plot_legend(labels)

        return axes

    def _xymax(self):
        labels = self._pv.keys()
        x = -np.inf
        y = -np.inf
        for label in labels:
            (lpv, lnpv) = self._xy(label)
            x = max(x, max(lpv))
            y = max(y, max(lnpv))
        return (x, y)

    def _xy(self, label):
        lpv = -np.log10(self._pv[label])
        lpv.sort()

        n = len(lpv)
        lnpv = np.linspace(1/(n+1), n/(n+1), n, endpoint=True)
        lnpv = np.flipud(-np.log10(lnpv))
        return (lnpv, lpv)

    def _plot_legend(self, labels):
        axes = self._axes
        fakes = []
        for l in labels:
            fake, = axes.plot([1,1], color=self._color[l], lw=3)
            fakes.append(fake)

        axes.legend(fakes, labels, bbox_to_anchor=(0., 1.02, 1., .102), loc=3,
                ncol=len(labels), mode="expand", borderaxespad=0.,
                frameon=False)
        for fake in fakes:
            fake.set_visible(False)

    def _plot_points(self, label, plot_top):
        axes = self._axes

        (lnpv, lpv) = self._xy(label)

        n = int(len(lnpv) * plot_top/100)

        rest = dict()
        if self._color[label]:
            rest['color'] = self._color[label]

        if self._properties[label]:
            rest.update(self._properties[label])

        axes.plot(lnpv[-n:], lpv[-n:], 'o',
                  clip_on=False, zorder=100, **rest)

        axes.set_ylabel(r'Observed -log10(P-value)')
        axes.set_xlabel(r'Expected -log10(P-value)')

    def _plot_confidence_band(self):
        axes = self._axes

        (bo, me, to) = _rank_confidence_band(self._max_size)
        bo = np.flipud(-np.log10(bo))
        me = np.flipud(-np.log10(me))
        to = np.flipud(-np.log10(to))

        x = y = me[0], me[-1]
        axes.plot(x, y, 'black')
        axes.fill_between(me, bo, to, lw=1.0,
                          edgecolor='black', facecolor='0.95',
                          clip_on=False)

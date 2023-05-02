import pickle
import numpy as np
from OperationSystem.AnalysisProcess.OperatorMethod.spatialFilter import TDCA
from mne.decoding import ReceptiveField
from sklearn.model_selection import train_test_split
from mne.decoding.receptive_field import _delay_time_series,_times_to_delays


class NRC(ReceptiveField):

    def __init__(self, srate, tmin=-0.5, tmax=1, alpha=0.9, fill_mean=True) -> None:

        self.tmin=tmin
        self.tmax=tmax
        self.srate=srate
        self.estimator = None
        self.alpha = alpha
        self.fill_mean = fill_mean

        pass

    def fit(self,R,S):

        epochNUM,chnNUM,_ = R.shape
        laggedLEN = len(_times_to_delays(self.tmin,self.tmax,self.srate))
        Kernel = np.zeros((epochNUM,chnNUM,laggedLEN))
        Cov_sr = np.zeros((epochNUM,chnNUM,laggedLEN))

        for epochINX,(epoch,sti) in enumerate(zip(R,S)):
            sti = sti[:,np.newaxis]
            laggedS = _delay_time_series(sti, self.tmin, self.tmax,self.srate,fill_mean=self.fill_mean).squeeze()

            # stimulation whitening
            Cov_ss = laggedS.T.dot(laggedS)
            u,sigma,v = np.linalg.svd(Cov_ss)
            for i in range(len(sigma)):
                if sum(sigma[0:len(sigma)-i]/sum(sigma)) < self.alpha:
                    sigma = 1/sigma
                    sigma[len(sigma)-i:] = 0
                    break
            sigma_app = np.diag(sigma)
            inv_C = u.dot(sigma_app).dot(v)

            for chnINX,chn in enumerate(epoch):

                Cov_sr[epochINX, chnINX] = (laggedS.T).dot(chn)
                Kernel[epochINX, chnINX] = (inv_C).dot(laggedS.T).dot(chn)

        self.kernel = Kernel
        self.Csr = Cov_sr

        self.trf = self.kernel.mean(axis=0)

        return self

    def predict(self, S):

        from scipy.stats import zscore
        R = []
        for s in S:
            s = zscore(s)

            s = s[:,np.newaxis]
            ss = _delay_time_series(s,tmin=self.tmin,tmax=self.tmax,sfreq=self.srate,fill_mean=True).squeeze()

            r = ss.dot(self.trf.T)
            # norm_r = zscore(r.T,axis=-1)
            R.append(r.T)

        return zscore(np.stack(R),axis=-1)


class Code2EEG():

    def __init__(self, S, srate=250, winLEN=1, tmin=0, tmax=0.5, estimator=0.98, scoring='corrcoef', padding=True, n_band=5, component=1) -> None:

        self.srate = srate
        self.tmin = tmin
        self.tmax = tmax
        self.winLEN = int(srate*winLEN)
        self.estimator = estimator
        self.scoring = scoring
        self.band = n_band
        self.component = component
        self.padding = padding
        self.padLEN = int(0.2*srate) if self.padding else 0

        self._loadSTI(S)

        pass

    def _loadSTI(self, *S):

        from scipy.stats import zscore

        # load STI as a class attibute
        STI, y = S[0]
        self.montage = np.unique(y)
        self.STI = np.stack([STI[y == i].mean(axis=0) for i in self.montage])
        # self.STI = zscore(self.STI, axis=-1)
        self.STI = self.STI[:, :self.winLEN]

        return

    def fit(self, X, y):

        self._classes = np.unique(y)

        # trim
        X = X[:, :, :self.winLEN]
        N = np.shape(X)[-1]
        # TDCA
        enhancer = TDCA(srate=self.srate, winLEN=N /
                        self.srate, montage=len(self._classes), n_band=self.band, n_components=self.component, lag=0)

        # input: enhanced response and the respective STI
        enhanced = enhancer.fit_transform(X, y)
        # reshaped enhance to (fb * components)
        STI = np.concatenate([self.STI[self.montage == i]
                              for i in self._classes])
        STI = np.tile(STI, self.component)

        regressor = NRC(srate=self.srate, tmin=self.tmin,
                        tmax=self.tmax, alpha=self.estimator)
        regressor.fit(R=enhanced, S=STI)

        self.regressor = regressor
        self.enhancer = enhancer
        self.enhanced = enhanced
        self.trf = regressor.trf

        return self

    def predict(self, S):

        # padding for VEP onset
        S = np.tile(S, self.component)
        pad = np.zeros((S.shape[0], self.padLEN))
        S = np.concatenate((pad, S), axis=-1)
        R_ = self.regressor.predict(S)

        # discard padding
        return R_[:, :, self.padLEN:]

    def score(self, S, R):

        from mne.decoding.receptive_field import _SCORERS
        # Create our scoring object
        scorer_ = _SCORERS[self.scoring]

        r_pred = self.predict(S)

        R_ = self.enhancer.transform(R)
        scores = []
        for (r_, r) in zip(r_pred, R_):

            score = scorer_(r.T, r_.T, multioutput='raw_values')
            scores.append(score)

        scores = np.stack(scores)

        return scores

if __name__ == '__main__':

    srate = 240
    expName = 'sweep'

    dir = 'datasets/%s.pkl' % expName
    winLENs = np.arange(0.2, 1, step=.2)
    with open(dir, "rb") as fp:
        wholeset = pickle.load(fp)

    sub = wholeset[1]

    chnNames = ['PZ', 'PO5', 'POZ', 'PO4', 'PO6', 'O1', 'OZ']
    chnINX = [sub['channel'].index(i) for i in chnNames]
    X = sub['wn']['X'][:, chnINX]
    y = sub['wn']['y']
    S = sub['wn']['STI']

    # reshape to class*block*chn*N
    X_ = np.stack(X[y == i] for i in np.unique(y))
    y_ = np.stack(y[y == i] for i in np.unique(y))

    # split conditions
    X_train, X_test, y_train, y_test = train_test_split(
        X_, y_, test_size=0.5, random_state=253)

    X_train, X_test = np.concatenate(
        X_train, axis=0), np.concatenate(X_test, axis=0)
    y_train, y_test = np.concatenate(
        y_train, axis=0), np.concatenate(y_test, axis=0)
    S_train, S_test = np.stack(
        [S[i-1] for i in y_train]), np.stack([S[i-1] for i in y_test])

    model = Code2EEG(srate=240, tmin=0, tmax=0.9, S=(
        S, np.unique(y)), component=2, estimator=0.8)
    model.fit(X_train, y_train)
    s = model.score(X_test, y_test)
    print(s)

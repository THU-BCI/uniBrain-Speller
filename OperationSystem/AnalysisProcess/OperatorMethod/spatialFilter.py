import numpy as np
import scipy.linalg as la
from sklearn.cross_decomposition import CCA
from sklearn.metrics import accuracy_score
from scipy import stats, signal
import math
from statsmodels.stats.weightstats import ttest_ind
import matplotlib.pyplot as plt

import logging

# configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.FileHandler('p_value.log')
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)


class TRCA():

    def __init__(self, n_components=1, n_band=1, montage=40, winLEN=2, lag=0.14, srate=250, sync_mode = "Normal", p_value = 0.01,
                 frequency = np.linspace(8, 15.8, num=40), phase = np.tile(np.arange(0, 2, 0.5)*math.pi, 10)):

        self.n_components = n_components
        self.n_band = n_band
        self.montage = montage
        self.frequency = frequency
        self.phase = phase
        self.srate = srate
        self.winLEN = round(self.srate*winLEN)
        self.lag = round(self.srate*lag)
        self.fb_coef = np.arange(1, n_band+1)[np.newaxis, :]**-1.25+0.25
        self.sync_mode = sync_mode
        self.p_value = p_value
        
    def test_plot_filter_banks(self, X):
        
        if len(X.shape) < 3:
            X = np.expand_dims(X, axis=0)

        # Choose a random epoch
        random_epoch = np.random.randint(0, X.shape[0])

        # Get the data for the first channel of the random epoch
        # raw_data = X[random_epoch, 0, self.lag:self.lag+self.winLEN]
        
        raw_data = X[random_epoch, 0, :]
        
        # Create a time array based on the sampling rate and window length
        time = np.arange(self.winLEN) / self.srate

        # Create a 3x2 grid for subplots
        plt.figure(figsize=(12, 8))

        # Plot the raw data on the left half
        plt.subplot(3, 2, 1)
        plt.plot(time, raw_data[self.lag:self.lag+self.winLEN])
        plt.title(f"Raw data for epoch {random_epoch} (channel 0)")
        plt.xlabel("Time (s)")
        plt.ylabel("Amplitude")


        # Plot the filtered data for each band on the right half
        n_bands_to_plot = 5
        for band in range(n_bands_to_plot):
            filtered_data = self.filterbank(raw_data[np.newaxis, np.newaxis, :], fbINX=band)

            plt.subplot(3, 2, band + 2)  # Position the subplot on the right half
            plt.plot(time, filtered_data[0, 0, self.lag:self.lag+self.winLEN])
            plt.title(f"Filtered data (channel 0, band {band})")
            plt.xlabel("Time (s)")
            plt.ylabel("Amplitude")

        # Adjust the layout and show the plot
        plt.tight_layout()
        plt.show()

            
    
    def fit(self, X, y):
        """
        Parameters
        ----------
        X : ndarray, shape (n_epochs, n_channels, n_times)
        y : array, shape (n_epochs,)
            The class for each epoch.
        Returns
        -------
        self : instance of TRCA
            Returns the modified instance.
        """
        # in case the data are too short for the filter banks
        short_t_length = 0.2 * self.srate
        if self.winLEN >= short_t_length:
            # crop test data according to predefined latency
            X = X[:, :, self.lag:self.lag+self.winLEN]
            
        self._classes = np.unique(y)

        self.filters = []
        self.evokeds = []
        
        for fbINX in range(self.n_band):
            # 每种信号都有不同的模版

            filter = []
            evokeds = []

            for classINX in self._classes:

                this_class_data = X[y == classINX]
                
                this_band_data = self.filterbank(
                    this_class_data, fbINX=fbINX)
                
                if self.winLEN < short_t_length:
                    this_band_data = this_band_data[:, :, self.lag:self.lag+self.winLEN]
                    
                evoked = np.mean(this_band_data, axis=0)
                evokeds.append(evoked)
                weight = self.computer_trca_weight(this_band_data)
                filter.append(weight[:, :self.n_components])

            self.filters.append(np.concatenate(filter, axis=-1))
            self.evokeds.append(np.stack(evokeds))

        self.filters = np.stack(self.filters)
        self.evokeds = np.stack(self.evokeds).transpose((1, 0, 2, 3))

        return self

    def transform(self, X, y):
        from scipy.stats import zscore
        """
        Parameters
        ----------
        X : array, shape (n_epochs, n_channels, n_times)
            The data.

        Returns
        -------
        X : ndarray
            shape is (n_epochs, n_sources, n_times).
        """

        enhanced = np.zeros((self.n_band, self.montage, self.winLEN))

        for classINX, classEvoked in enumerate(self.evokeds):
            for fbINX, (filter, fb) in enumerate(zip(self.filters, classEvoked)):
                enhance = np.dot(fb.T, filter[:, classINX])
                enhanced[fbINX, classINX] = enhance

        enhanced = zscore(enhanced, axis=-1)

        return enhanced

    def fit_transform(self, X, y):

        return self.fit(X, y).transform(X, y)

    def predict(self, X, p = 0.01, mode = "Normal"):

        if len(X.shape) < 3:
            X = np.expand_dims(X, axis=0)

        # in case the data are too short for the filter banks
        short_t_length = 0.2 * self.srate
        if self.winLEN >= short_t_length:
            # crop test data according to predefined latency
            X = X[:, :, self.lag:self.lag+self.winLEN]
            
        

        result = []

        H = np.zeros(X.shape[0])

        self.rho = np.zeros((X.shape[0], self.montage))

        for epochINX, epoch in enumerate(X):

            r = np.zeros((self.n_band, self.montage))

            for fbINX in range(self.n_band):

                epoch_band = np.squeeze(self.filterbank(epoch, fbINX))
                if self.winLEN < short_t_length:
                    epoch_band = epoch_band[:, self.lag:self.lag+self.winLEN]
                t_sample = epoch_band.shape[1]
                
                for (classINX, evoked) in zip(np.arange(self.montage), self.evokeds):
                    
                    template = np.squeeze(evoked[fbINX, :, :t_sample])
                    w = np.squeeze(self.filters[fbINX, :])
                    rtemp = np.corrcoef(
                        np.dot(epoch_band.T, w).reshape(-1), np.dot(template.T, w).reshape(-1))
                    r[fbINX, classINX] = np.real(rtemp[0, 1])
                    


            rho = np.dot(self.fb_coef, r)

            self.rho[epochINX] = rho
            # hypothesis testing
            target = np.nanargmax(rho)
            rhoNoise = np.delete(rho, target)
            rhoNoise = np.delete(rhoNoise, np.isnan(rhoNoise))
            _, H[epochINX], _ = ttest_ind(
                rhoNoise, [rho[0, target]], alternative='smaller')
        
            if mode == "Normal":
                result.append(self._classes[target])
            else: # Dynamic window
                if H[epochINX] > p:
                    result.append(None)
                    # print("result FAILED, in p-value #{:.4f}#".format(H[epochINX]))
                else:
                    result.append(self._classes[target])
                    # message = "result PASSED, in p-value #{:.4f}#".format(H[epochINX])
                    # print(message)
                    # logger.info(message)

        self.confidence = H
        self.predicted = np.stack(result)
        return np.stack(result)

    def score(self, X, y):

        return accuracy_score(y, self.predict(X))

    def dyStopping(self, X, former_win):

        # 判断要设置什么窗
        srate = self.srate
        p_val = 0.0025

        dyStopping = np.arange(0.4, former_win+0.1, step=0.2)

        for ds in dyStopping:

            ds = int(ds*srate)
            self.predict(X[:, :, :ds+self.lag])

            score = self.confidence < p_val
            pesudo_acc = np.sum(score != 0)/len(score)
            print('mean confidence:', self.confidence.mean())
            print('pesudo_acc {pesudo_acc} %'.format(pesudo_acc=pesudo_acc))

            if self.confidence.mean() < p_val:
                boostWin = ds
                break

        # 难分的epoch下一次继续
        n = np.argsort(self.confidence)
        difficult = X[n[-5:]]

        if not 'boostWin' in locals().keys():
            boostWin = int(dyStopping[-1]*srate)

        return (boostWin/srate), difficult

    def filterbank(self, x, fbINX):

        passband = [6, 14, 22, 30, 38, 46, 54, 62, 70, 78]
        stopband = [4, 10, 16, 24, 32, 40, 48, 56, 64, 72]

        nrate = self.srate/2

        Wp = [passband[fbINX]/nrate, 90/nrate]
        Ws = [stopband[fbINX]/nrate, 100/nrate]

        # design filter parameters
        [N, Wn] = signal.cheb1ord(Wp, Ws, 3, 40)        
        [B, A] = signal.cheby1(N, 0.5, Wn, 'bandpass')

        if len(np.shape(x)) == 2:
            x = x[np.newaxis, :, :]

        # filtering
        filtered = signal.filtfilt(B, A, x, axis=-1)
        

        return filtered

    def computer_trca_weight(self, eeg):
        """
        Input:
            eeg : Input eeg data (# of targets, # of channels, Data length [sample])
        Output:
            W : Weight coefficients for electrodes which can be used as a spatial filter.
        """
        epochNUM, self.channelNUM, _ = eeg.shape

        S = np.zeros((self.channelNUM, self.channelNUM))

        for epoch_i in range(epochNUM):

            x1 = np.squeeze(eeg[epoch_i, :, :])
            # x1 = x1 - np.mean(x1, axis=1, keepdims=True)
            
            x1 = (x1 - np.mean(x1, axis=1, keepdims=True)) / np.max(np.abs(x1))
            

            for epoch_j in range(epoch_i+1, epochNUM):
                x2 = np.squeeze(eeg[epoch_j, :, :])
                # x2 = x2 - np.mean(x2, axis=1, keepdims=True)
                x2 = (x2 - np.mean(x2, axis=1, keepdims=True)) / np.max(np.abs(x2))
                S = S + np.dot(x1, x2.T) + np.dot(x2, x1.T)

        UX = np.stack([eeg[:, i, :].ravel() for i in range(self.channelNUM)])
        UX = UX - np.mean(UX, axis=1, keepdims=True)
        Q = np.dot(UX, UX.T)
        
        # eye = np.eye(self.channelNUM)
        # C = np.linalg.inv(Q+eye).dot(S)
        C = np.linalg.inv(Q).dot(S)
        _, W = np.linalg.eig(C)

        return W


class fbCCA():
    def __init__(self, frequency, n_components=1, n_band=5, srate=250, conditionNUM=20, lag=35, winLEN=2):
        self.n_components = n_components
        self.n_band = n_band
        self.srate = srate
        self.conditionNUM = conditionNUM
        self.montage = np.linspace(
            0, conditionNUM-1, conditionNUM).astype('int64')
        # self.frequency_info = np.linspace(8, 17.5, num=self.conditionNUM)
        self.frequency_info = frequency
        self.lag = round(self.srate*lag)
        self.winLEN = round(self.srate*winLEN)

    def fit(self, X=[], y=[]):

        epochLEN = self.winLEN

        self._classes = np.unique(y)
        sineRef = self.get_reference(
            self.srate, self.frequency_info, n_harmonics=5, data_len=epochLEN)

        self.evokeds = sineRef

        return self

    def predict(self, X, p = 0.01, mode = "Normal"):

        if len(X.shape) < 3:
            X = np.expand_dims(X, axis=0)


        # in case the data are too short for the filter banks
        short_t_length = 0.2 * self.srate
        if self.winLEN >= short_t_length:
            # crop test data according to predefined latency
            X = X[:, :, self.lag:self.lag+self.winLEN]
            
        # X = X[:, :, self.lag:self.lag+self.winLEN]

        result = []
        evokeds = self.evokeds[:,:,:X.shape[-1]]

        H = np.zeros(X.shape[0])
        corr = np.zeros(X.shape[0])

        fb_coefs = np.expand_dims(
            np.arange(1, self.n_band+1)**-1.25+0.25, axis=0)

        for epochINX, epoch in enumerate(X):

            r = np.zeros((self.n_band, self.conditionNUM))
            cca = CCA(n_components=1)
            for fbINX in range(self.n_band):
                epoch_band = np.squeeze(
                    self.filterbank(epoch, self.srate, fbINX))
                
                if self.winLEN < short_t_length:
                    epoch_band = epoch_band[:, self.lag:self.lag+self.winLEN]
                    
                for (classINX, evoked) in zip(self.montage, evokeds):
                    u, v = cca.fit_transform(evoked.T, epoch_band.T)
                    rtemp = np.corrcoef(u.T, v.T)
                    r[fbINX, classINX] = rtemp[0, 1]
            rho = np.dot(fb_coefs, r)

            # snr = np.power(rho,2)/(1-np.power(rho,2)) * featureNUM
            target = np.nanargmax(rho)
            # snrNoise = np.delete(snr,target)
            rhoNoise = np.delete(rho, target)

            _, H[epochINX], _ = ttest_ind(rhoNoise, [rho[0, target]])
            corr[epochINX] = rho[0, target]

            if mode == "Normal":
                result.append(self._classes[target])
            else: # Dynamic window
                if H[epochINX] > p:
                    result.append(None)
                    # print("result FAILED, in p-value #{:.4f}#".format(H[epochINX]))
                else:
                    result.append(self._classes[target])
                    # message = "result PASSED, in p-value #{:.4f}#".format(H[epochINX])
                    # print(message)
                    # logger.info(message)


        self.confidence = H
        self.corr = corr

        return np.stack(result)

    def filterbank(self, x, srate, freqInx):

        passband = [6, 14, 22, 30, 38, 46, 54, 62, 70, 78]
        stopband = [4, 10, 16, 24, 32, 40, 48, 56, 64, 72]

        srate = srate/2
        Wp = [passband[freqInx]/srate, 90/srate]
        Ws = [stopband[freqInx]/srate, 100/srate]
        [N, Wn] = signal.cheb1ord(Wp, Ws, 3, 40)
        [B, A] = signal.cheby1(N, 0.5, Wn, 'bandpass')

        filtered_signal = np.zeros(np.shape(x))
        if len(np.shape(x)) == 2:
            for channelINX in range(np.shape(x)[0]):
                filtered_signal[channelINX, :] = signal.filtfilt(
                    B, A, x[channelINX, :])
            filtered_signal = np.expand_dims(filtered_signal, axis=-1)
        else:
            for epochINX, epoch in enumerate(x):
                for channelINX in range(np.shape(epoch)[0]):
                    filtered_signal[epochINX, channelINX, :] = signal.filtfilt(
                        B, A, epoch[channelINX, :])

        return filtered_signal

    def get_reference(self, srate, frequency_info, n_harmonics, data_len):

        t = np.arange(0, (data_len/srate), 1/srate)
        reference = []
        frequency_info = np.squeeze(frequency_info)

        for j in range(n_harmonics):
            harmonic = [np.array([np.sin(2*np.pi*i*frequency_info*(j+1)) for i in t]),
                        np.array([np.cos(2*np.pi*i*frequency_info*(j+1)) for i in t])]
            reference.append(harmonic)
        # reference = np.stack(reference[i] for i in range(len(reference)))
        reference = np.stack([reference[i] for i in range(len(reference))])
        reference = np.reshape(
            reference, (2*n_harmonics, data_len, len(frequency_info)))
        reference = np.transpose(reference, (-1, 0, 1))

        return reference

    def score(self, X, y):

        return accuracy_score(y, self.predict(X))


class TDCA(TRCA):

    def __init__(self, n_components=1, n_band=1, montage=40, winLEN=2, lag=0.14, srate=250):
        super().__init__(n_components, n_band, montage, winLEN, lag, srate)
        self.fb_coef = np.arange(1, n_band+1)[np.newaxis, :]**-1.25+0.25

    def fit(self, X, y):
        # X: 160*9*750
        self._classes = np.unique(y)
        self.filters = []
        self.evokeds = []
        self.epochNUM, self.channelNUM, N = X.shape

        # 先子带滤波，否则会引入很大计算量
        X = self.augmentation(X)

        # 滤波之后再截取latency
        X = X[..., self.lag:self.lag+self.winLEN]

        X = np.transpose(X, axes=(1, 0, -2, -1))

        augumentX = []

        for fbX in X:

            augumentClass = []

            for classINX in self._classes:

                this_class_data = fbX[y == classINX]

                augumentEpoch = []

                for epoch in this_class_data:

                    augumentEpoch.append(epoch)

                augumentClass.append(np.stack(augumentEpoch))

            augumentX.append(augumentClass)

        # augumentX:
        # 如果每个condition的数目不一样，就不能stack
        # augumentX = np.stack(augumentX)

        self.computer_tdca_weight(augumentX)

        return self

    def transform(self, X, y=None):
        from scipy.stats import zscore
        """
        Parameters
        ----------
        X : array, shape (n_epochs, n_channels, n_times)
            The data.

        Returns
        -------
        X : ndarray
            shape is (n_epochs, n_sources, n_times).
        """
        X = X[:, :, self.lag:self.lag+self.winLEN]

        if y is None:
            y = np.arange(X.shape[0])

        n_class = len(np.unique(y))
        enhanced = np.zeros(
            (n_class, self.n_band, self.n_components, self.winLEN))

        fbed_X = self.augmentation(X)
        for conditionINX, condition in enumerate(np.unique(y)):
            classEvoked = fbed_X[y == condition].mean(axis=0)
            for fbINX, (fb, filter) in enumerate(zip(classEvoked, self.filters)):
                enhance = fb.T.dot(filter)
                enhanced[conditionINX, fbINX] = enhance.T
        # reshape
        enhanced = np.reshape(enhanced, (n_class, self.n_band, -1))

        return zscore(enhanced, axis=-1)

    def predict(self, X, p = 0.01, mode = "Normal"):

        if len(X.shape) < 3:
            X = np.expand_dims(X, axis=0)

        result = []

        H = np.zeros(X.shape[0])

        X = self.augmentation(X)

        X = X[..., self.lag:self.lag+self.winLEN]

        self.rho = np.zeros((X.shape[0], self.montage))

        for epochINX, epoch in enumerate(X):

            r = np.zeros((self.n_band, self.montage))

            for (classINX, evoked) in zip(np.arange(self.montage), self.evokeds):

                for fbINX, (fbEvoked, fbEpoch, filter) in enumerate(zip(evoked, epoch, self.filters)):

                    rtemp = np.corrcoef((
                        np.dot(fbEpoch.T, filter).reshape(-1),
                        np.dot(fbEvoked.T, filter).reshape(-1)
                    ))
                    r[fbINX, classINX] = rtemp[0, 1]

            rho = np.dot(self.fb_coef, r)
            self.rho[epochINX] = rho

            target = np.nanargmax(rho)
            rhoNoise = np.delete(rho, target)
            rhoNoise = np.delete(rhoNoise, np.isnan(rhoNoise))
            _, H[epochINX], _ = ttest_ind(rhoNoise, [rho[0, target]])
            
            if mode == "Normal":
                result.append(self._classes[target])
            else:
                if H[epochINX] > p:
                    result.append(None)
                else:
                    result.append(self._classes[target])

        self.confidence = H
        self.predicted = np.stack(result)
        
        return np.stack(result)

    def computer_tdca_weight(self, augmentX):

        augmentEvoked = []
        for fbs in augmentX:
            augmentEvoked.append([con.mean(axis=0) for con in fbs])
        # augmentEvoked: 5*40*9*478
        augmentEvoked = np.stack(augmentEvoked)

        for (fbEvoked, fbEpochs) in zip(augmentEvoked, augmentX):
            # norm
            # fbEvoked:40*9*478; fbEpochs:40*9*478
            fbEvoked = fbEvoked-np.mean(fbEvoked, axis=-1, keepdims=True)
            fbEvokedFeature = np.mean(fbEvoked, axis=0, keepdims=True)
            betwClass = fbEvoked-fbEvokedFeature
            betwClass = np.concatenate(betwClass, axis=1)
            # norm
            fbEpochs = [
                this_class-np.mean(this_class, axis=-1, keepdims=True) for this_class in fbEpochs
            ]
            allClassEvoked = [
                this_class-np.mean(this_class, axis=0, keepdims=True) for this_class in fbEpochs
            ]

            allClassEvoked = [np.transpose(this_class, axes=(
                1, 2, 0)) for this_class in allClassEvoked]
            allClassEvoked = [np.reshape(
                this_class, (self.channelNUM, -1), order='F') for this_class in allClassEvoked]
            allClassEvoked = np.hstack(allClassEvoked)

            Hb = betwClass/math.sqrt(self.montage)
            Hw = allClassEvoked/math.sqrt(self.epochNUM)
            self.Hb = Hb
            self.Hw = Hw
            Sb = np.dot(Hb, Hb.T)
            # Sw = np.dot(Hw, Hw.T)+0.001*np.eye(Hw.shape[0])
            Sw = np.dot(Hw, Hw.T)

            # inv(Sw)*B
            C = np.linalg.inv((Sw)).dot(Sb)
            _, W = np.linalg.eig(C)
            _, W = la.eig(C)

            # tmd又是反的？
            self.filters.append(W[:, :self.n_components])

        self.evokeds = np.transpose(augmentEvoked, axes=(1, 0, -2, -1))

        return

    def augmentation(self, X):

        # from scipy.stats import zscore

        augmentX = []
        for epoch in X:
            fbedEpoch = []
            for fbINX in range(self.n_band):
                fbEpoch = self.filterbank(epoch, fbINX)
                fbedEpoch.append(fbEpoch)
            fbedEpoch = np.concatenate(fbedEpoch, axis=-1)
            augmentX.append(fbedEpoch)

        augmentX = np.stack(augmentX)
        augmentX = np.transpose(augmentX, axes=(0, -1, 1, 2))

        # augmentX = zscore(augmentX,axis=-1)

        return augmentX

    def filterbank(self, x, fbINX):

        fbPara = [[(6, 90), (4, 100)],  # passband, stopband freqs [(Wp), (Ws)]
                  [(14, 90), (10, 100)],
                  [(22, 90), (16, 100)],
                  [(30, 90), (24, 100)],
                  [(38, 90), (32, 100)], ]

        nrate = self.srate/2

        pBand, sBand = fbPara[fbINX]
        Wp = [pBand[0]/nrate, pBand[1]/nrate]
        Ws = [sBand[0]/nrate, sBand[1]/nrate]

        # design filter parameters
        [N, Wn] = signal.cheb1ord(Wp, Ws, 3, 40)
        [B, A] = signal.cheby1(N, 0.5, Wn, 'bandpass')

        if len(np.shape(x)) == 2:
            x = x[np.newaxis, :, :]
        # filtering
        filtered = signal.filtfilt(B, A, x, axis=-1)

        return np.transpose(filtered, (1, 2, 0))


if __name__ == '__main__':
    import os
    import pickle
    import sys
    current_path = os.getcwd()
    sys.path.append(current_path)
    file_path = "Result\\limjiale\\data\\ssvep_Keyboard 43 keys_20230409_121613_test.pkl"

    with open(file_path, "rb") as f:
        data = pickle.load(f)

    print(len(data['X']))

    texts = [
        "⇧A ZEBRA, 2 MICE, 5 DOGS JUMPED.↵",
        "3 KIND CATS, 6 FROGS, 9 FISH SWIM.↵",
        "⇧QUIETLY, 8 ELEPHANTS WALK BY 4 TREES.↵",
        "⇧VEXING BUGS ON 1 LEAF, 0 HARM DONE.↵",
        "7 HENS LAY GOLDEN EGGS, X MARKS SPOT.↵",
        "⇧WHY DID UPTON, THE 1ST, BUY 9←8 PLUMS⇧/↵",
    ]

    total_characters = sum(len(text) for text in texts)

    print(f"Total number of characters: {total_characters}")

    for y in data['y']:
        print(y)



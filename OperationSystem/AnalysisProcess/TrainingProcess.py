from OperationSystem.AnalysisProcess.BasicAnalysisProcess import BasicAnalysisProcess
from OperationSystem.AnalysisProcess.OperatorMethod.spatialFilter import TRCA,TDCA,fbCCA
import numpy as np
import pandas as pd
import pickle
import os
import pickle
import matplotlib.pyplot as plt
import json
import time

class TrainingProcess(BasicAnalysisProcess):
    def __init__(self) -> None:
        self.controller = None
        super().__init__()

    def run(self):

        # Training process, event labels are also passed in
        
        # Synchronous system
        while True:
            epoch, event = self.streaming.readFixedData(0, self.winLEN+self.lag)
            time.sleep(0.04)
            if epoch is not None:
                self.streaming.eventExist = False
                break
            if self.messenger.state.control_state == 'EXIT':
                return
            
        result = 0

        # Report the result
        self.controller.report(result)

        # Store current epoch
        self._collectTrain(epoch, event)

        self.logger.info('Training in process, No.%s epoch done, event:%s' % (self.controller.currentEpochINX, event))

        # Train the model
        if self.controller.trainFlag is True:
            self.trainModel()
            self.performance(self.controller.trainData['X'], self.controller.trainData['y'])
            self.viz()

        self.controller.current_process = self.controller.wait_process
        self.messenger.state.current_detect_state = 'INIT'
        return

    def load_checkpoint(self, checkpoint_path):
        with open(checkpoint_path, 'rb') as f:
            checkpoint = pickle.load(f)

        for key, value in checkpoint.items():
            setattr(self, key, value)

    def _collectTrain(self, x, y):
        epochINX = self.controller.currentEpochINX

        # X: epoch * chn * T
        self.controller.trainData['X'].append(x[np.newaxis, :, :])
        self.controller.trainData['y'].append(y)

        if (epochINX + 1) % self.targetNUM == 0:
            self.controller.currentBlockINX += 1

            _file_name = f'{self.prefix_with_time}train.pkl'
            method_name = f'{self.feature_algo}_'
            file_name = _file_name.replace(method_name, "")

            file_path = os.path.join(self.savepath, 'data', file_name)

            with open(file_path, "wb+") as fp:
                pickle.dump(self.controller.trainData, fp,
                            protocol=pickle.HIGHEST_PROTOCOL)

            # save a json file
            json_file_path = os.path.splitext(file_path)[0] + ".json"

            data = {
                "person_name": self.personName,
                "lag": self.lag,
                "feature_algo": self.feature_algo,
                "n_band": self.n_band,
                "srate": self.srate,
                "paradigm": self.paradigm,
                "block_count": self.controller.currentBlockINX,
                "target_count": self.targetNUM
            }

            with open(json_file_path, "w") as f:
                json.dump(data, f, indent=4)

        self.controller.currentEpochINX += 1

        if (epochINX + 1) >= self.totalTargetNUM:
            self.controller.trainFlag = True

        return

    def performance(self, X, y):
        from tqdm import tqdm
        from sklearn.model_selection import LeaveOneOut
        from OperationSystem.AnalysisProcess.OperatorMethod.utils import ITR

        if self.progress_manager is not None:
            self.progress_manager["text"] = "Evaluating offline performance..."
            self.progress_manager["value"] = 101

        # X, y = np.concatenate(X), np.concatenate(y)
        X, y = np.squeeze(X), np.squeeze(y)
        print(X.shape)
        print(y.shape)
        print(np.unique(y))
        X = np.stack([X[y == i] for i in np.unique(y)])
        y = np.stack([y[y == i] for i in np.unique(y)])

        X = np.transpose(X, axes=(1, 0, -2, -1))
        y = np.transpose(y, axes=(-1, 0))

        loo = LeaveOneOut()
        loo.get_n_splits(X)
        frames = []

        winLenArray = np.round(np.arange(0.1, self.winLEN + 0.1, 0.1), 2)
        total_iterations = loo.get_n_splits(X) * len(winLenArray)
        current_iteration = 0

        # Check the length of X here
        if X.shape[0] == 1:
            train_index = [0]
            test_index = [0]
            loo_splits = [(train_index, test_index)]  # list containing a single tuple
            tqdm_description = "Single sample"
        else:
            loo_splits = loo.split(X)
            tqdm_description = "Leave One Out"

        for cv, (train_index, test_index) in tqdm(enumerate(loo_splits)):
            Xtrain, X_test = np.concatenate(X[train_index]), np.concatenate(X[test_index])
            ytrain, y_test = np.concatenate(y[train_index]), np.concatenate(y[test_index])

            for winLEN in winLenArray:
                if self.feature_algo == "TRCA":
                    model = TRCA(montage=self.targetNUM, winLEN=winLEN, srate=self.srate, sync_mode=self.sync_mode,
                                p_value=self.p_value, frequency=self.frequency, phase=self.phase, n_band=5, lag=self.lag)
                elif self.feature_algo == "FBCCA":
                    model = fbCCA(frequency=self.frequency, winLEN=winLEN, srate=self.srate, conditionNUM=self.targetNUM, lag=self.lag)
                    

                model.fit(Xtrain, ytrain)
                if self.feature_algo == "TRCA" and np.iscomplexobj(model.filters):
                    print(f"Under window length of {winLEN}s, model's filters are complex")

                accuracy = model.score(X_test, y_test)
                itr = ITR(self.targetNUM, accuracy, winLEN)
                y_pred = model.predict(X_test)
                individual_accuracies = [np.mean(y_pred[y_test == i] == i) for i in np.unique(y_test)]

                f = pd.DataFrame({
                    'subject': [self.personName],
                    'Window Length': [winLEN],
                    'Accuracy': [accuracy],
                    'paradigm': [self.paradigm],
                    'cv': [cv],
                    'ITR': [itr],
                    'Individual Accuracies': [individual_accuracies]
                })

                frames.append(f)


                if self.progress_manager is not None:
                    current_iteration += 1
                    progress_percentage = (current_iteration / total_iterations) * 100
                    self.progress_manager["value"] = progress_percentage

        df = pd.concat(frames, axis=0, ignore_index=True)
        file_name = f'{self.prefix_with_time}offline.csv'
        df.to_csv(os.path.join(self.savepath, 'record', file_name))


    def viz(self):
        import seaborn as sns
        import matplotlib.pyplot as plt

        if self.progress_manager != None:
            self.progress_manager["text"] = f"Plotting graphs..."
            self.progress_manager["value"] = 101

        frames = []
        d = os.listdir(self.savepath + os.sep + 'record')
        file_name = f'{self.prefix_with_time}offline.csv'
        file_path = os.path.join(self.savepath, 'record', file_name)

        df = pd.read_csv(file_path)
        frames.append(df)
        frames = pd.concat(frames, axis=0, ignore_index=True)

        # filter data for possible wrong ITRs
        frames['ITR'] = frames['ITR'].apply(lambda x: 0 if x < 0 else x)

        # DEBUG
        # print(frames.to_string())

        sns.set_theme(style='ticks')

        # Create subplots with two rows and one column
        fig, axes = plt.subplots(2, 1)

        # Plot Accuracy vs Window Length on the first subplot
        sns.lineplot(ax=axes[0], data=frames, x='Window Length', y='Accuracy', hue='paradigm')
        axes[0].set_title(self.feature_algo + ': Accuracy over Window Length')

        # Plot ITR vs Window Length on the second subplot
        sns.lineplot(ax=axes[1], data=frames, x='Window Length', y='ITR', hue='paradigm')
        axes[1].set_title(self.feature_algo + ': ITR over Window Length')

        plt.tight_layout()

        file_name = f'{self.prefix_with_time}offline.png'
        file_path = os.path.join(self.savepath, 'images', file_name)

        fig.savefig(file_path, dpi=400)

        # plt.show()
        plt.close()


    def trainModel(self):
        if self.progress_manager != None:
            self.progress_manager["text"] = f"Training {self.feature_algo} model..."
        if self.feature_algo == "TRCA":
            model = TRCA(montage=self.targetNUM, winLEN=self.winLEN, srate=self.srate, sync_mode=self.sync_mode,
                         p_value=self.p_value, frequency=self.frequency, phase=self.phase, n_band=5, lag=self.lag)
        elif self.feature_algo == "FBCCA":
            model = fbCCA(frequency=self.frequency, winLEN=self.winLEN, srate=self.srate,
                          conditionNUM=self.targetNUM, lag=self.lag)
        elif self.feature_algo == "TDCA":
            model = TDCA(winLEN=self.winLEN, srate=self.srate)

        trainX = self.controller.trainData['X']
        trainy = self.controller.trainData['y']

        trainX, trainy = np.squeeze(trainX), np.squeeze(trainy)

        model.fit(trainX, trainy)

        self.controller.testing_process.algorithm = model

        if self.progress_manager != None:
            self.progress_manager["text"] = f"Saving {self.feature_algo} model..."
        file_name = f'{self.prefix}Model.pkl'
        file_path = os.path.join(self.savepath, 'models', file_name)
        with open(file_path, "wb+") as fp:
            pickle.dump(model, fp, protocol=pickle.HIGHEST_PROTOCOL)

        # save a json file
        json_file_path = os.path.splitext(file_path)[0] + ".json"

        data = {
            "person_name": self.personName,
            "lag": self.lag,
            "feature_algo": self.feature_algo,
            "n_band": self.n_band,
            "srate": self.srate,
            "paradigm": self.paradigm,
            "block_count": self.controller.currentBlockINX,
            "target_count": self.targetNUM
        }

        with open(json_file_path, "w") as f:
            json.dump(data, f, indent=4)
        
        
            
        return
    
    def showReport(self):
        pass


    
    
if __name__ == '__main__':
    import seaborn as sns
    import matplotlib.pyplot as plt

    # file_name_1 = 'Result\\miaoyining\\record\\ssvep_Mouse 13 keys HS_FBCCA_20230418_200550_offline.csv'
    # file_name_1 = 'Result\\miaoyining\\record\\ssvep_Mouse 13 keys HS_FBCCA_20230418_200550_offline.csv'
    # file_name_1 = 'Result\\miaoyining\\record\\ssvep_Keyboard 43 keys HS_TRCA_20230417_154540_offline.csv'
    file_name_1 = 'Result\\miaoyining\\record\\ssvep_Keyboard 43 keys HS_FBCCA_20230418_211118_offline.csv'
    
    # Result\miaoyining\record\ssvep_Mouse 13 keys HS_FBCCA_20230418_200550_offline.csv
    # file_name_2 = 'Result\\Zheng Jia Han\\record\\ssvep_Keyboard 43 keys HS_FBCCA_20230418_202642_offline.csv'
    # file_name_2 = 'Result\\Zheng Jia Han\\record\\ssvep_Mouse 13 keys HS_FBCCA_20230418_202404_offline.csv'
    # file_name_2 = 'Result\\Zheng Jia Han\\record\\ssvep_Keyboard 43 keys HS_TRCA_20230417_135334_offline.csv'
    file_name_2 = 'Result\\Zheng Jia Han\\record\\ssvep_Keyboard 43 keys HS_FBCCA_20230418_202642_offline.csv'
    

    df1 = pd.read_csv(file_name_1)
    df2 = pd.read_csv(file_name_2)

    sns.set_theme(style='ticks')
    f, ax = plt.subplots()

    # 绘制第一条线，并指定图例标签
    sns.lineplot(data=df1, x='Window Length', y='Accuracy', label='Subject 1')

    # 绘制第二条线，并指定图例标签
    sns.lineplot(data=df2, x='Window Length', y='Accuracy', label='Subject 2')

    # 添加标题
    plt.title('FBCCA')

    # 去掉x轴标签
    ax.set(xlabel=None)

    # 显示图例
    plt.legend()

    # 调整布局
    plt.tight_layout()

    file_name = 'Subject vs FBCCA 43 Acc.png'
    outputPath = os.path.join("C:\\Users\\taiwa\\Documents\\GitHub\\result",file_name)

    f.savefig(outputPath, dpi=400)

    plt.close()


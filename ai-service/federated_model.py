import numpy as np


class FederatedRandomForest:

    def __init__(self, estimators, feature_names, classes):
        self.estimators = estimators
        self.feature_names = feature_names
        self.classes_ = np.array(classes)
        self.n_features_in_ = len(feature_names)

    def predict_proba(self, X):

        X = np.asarray(X)

        all_probabilities = []

        for tree in self.estimators:

            tree_proba = tree.predict_proba(X)

            aligned_proba = np.zeros(
                (X.shape[0], len(self.classes_))
            )

            for local_index, local_class in enumerate(tree.classes_):

                global_index = np.where(
                    self.classes_ == local_class
                )[0][0]

                aligned_proba[:, global_index] = (
                    tree_proba[:, local_index]
                )

            all_probabilities.append(aligned_proba)

        if not all_probabilities:
            raise RuntimeError(
                "Federated Random Forest contains no trees."
            )

        return np.mean(
            all_probabilities,
            axis=0
        )

    def predict(self, X):

        probabilities = self.predict_proba(X)

        indexes = np.argmax(
            probabilities,
            axis=1
        )

        return self.classes_[indexes]

    def get_feature_importances(self):

        if not self.estimators:

            return np.zeros(
                self.n_features_in_
            )

        importances = np.array([
            tree.feature_importances_
            for tree in self.estimators
        ])

        return np.mean(
            importances,
            axis=0
        )
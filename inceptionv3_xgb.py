import numpy as np
import os
import pandas as pd
import random
from tqdm import tqdm
import xgboost as xgb
import tensorflow as tf
from keras.applications.inception_v3 import InceptionV3
from keras.models import Model
from keras.preprocessing import image
from keras.applications.inception_v3 import preprocess_input
from keras.layers import Flatten, Input

import scipy
from sklearn.metrics import fbeta_score

random_seed = 0
random.seed(random_seed)
np.random.seed(random_seed)

n_classes = 17

train_path = "/mnt/home/dunan/Learn/Kaggle/planet_amazon/train-jpg/"
test_path = "/mnt/home/dunan/Learn/Kaggle/planet_amazon/test-jpg/"
train = pd.read_csv("/mnt/home/dunan/Learn/Kaggle/planet_amazon/train_v2.csv")
test = pd.read_csv("/mnt/home/dunan/Learn/Kaggle/planet_amazon/sample_submission_v2.csv")

flatten = lambda l: [item for sublist in l for item in sublist]
labels = list(set(flatten([l.split(' ') for l in train['tags'].values])))

label_map = {'agriculture': 0, 'artisinal_mine': 1, 'bare_ground': 2, 'blooming': 3, 'blow_down': 4, 'clear': 5,
             'cloudy': 6, 'conventional_mine': 7, 'cultivation': 8, 'habitation': 9, 'haze': 10, 'partly_cloudy': 11,
             'primary': 12, 'road': 13, 'selective_logging': 14, 'slash_burn': 15, 'water': 16}
inv_label_map = {i: l for l, i in label_map.items()}

# use vgg 16 model extract feature from fc1 layer
model = InceptionV3(weights='imagenet', include_top=False, pooling = "avg")

X_train = []
y_train = []

for f, tags in tqdm(train.values[:], miniters=1000):
    # preprocess input image
    img_path = train_path + "{}.jpg".format(f)
    img = image.load_img(img_path, target_size=(299, 299))
    x = image.img_to_array(img)
    x = np.expand_dims(x, axis=0)
    x = preprocess_input(x)

    # generate feature [2048]
    features = model.predict(x)
    #(features.shape)
    features_reduce =  features.squeeze()
    #print(features_reduce.shape)
    X_train.append(features_reduce)

    # generate one hot vecctor for label

    targets = np.zeros(n_classes)
    for t in tags.split(' '):
        targets[label_map[t]] = 1
    y_train.append(targets)

X = np.array(X_train)
y = np.array(y_train, np.uint8)

X_test = []

for f, tags in tqdm(test.values[:], miniters=1000):
    img_path = test_path + "{}.jpg".format(f)
    img = image.load_img(img_path, target_size=(299, 299))
    x = image.img_to_array(img)
    x = np.expand_dims(x, axis=0)
    x = preprocess_input(x)

    # generate feature [2048]
    features = model.predict(x)
    features_reduce = features.squeeze()
    X_test.append(features_reduce)



X_test = np.array(X_test)
y_pred = np.zeros((X_test.shape[0], n_classes))

print('Training and making predictions')
for class_i in tqdm(range(n_classes), miniters=1):
    model = xgb.XGBClassifier(max_depth=5, learning_rate=0.1, n_estimators=100, \
                              silent=True, objective='binary:logistic', nthread=-1, \
                              gamma=0, min_child_weight=1, max_delta_step=0, \
                              subsample=1, colsample_bytree=1, colsample_bylevel=1, \
                              reg_alpha=0, reg_lambda=1, scale_pos_weight=1, \
                              base_score=0.5, seed=random_seed, missing=None)
    model.fit(X, y[:, class_i])
    y_pred[:, class_i] = model.predict_proba(X_test)[:, 1]

preds = []
scores = []
for y_pred_row in y_pred:
    result = []
    full_result = []
    for i, value in enumerate(y_pred_row):
        full_result.append(str(i))
        full_result.append(str(value))
        if value > 0.21:
            result.append(labels[i])
    preds.append(" ".join(result))
    scores.append(" ".join(full_result))

subm = pd.DataFrame()
subm['image_name'] = test.image_name.values
subm['tags'] = preds
subm.to_csv('/mnt/home/dunan/Learn/Kaggle/planet_amazon/inceptionv3_submission.csv', index=False)

orginin = pd.DataFrame()
orginin['image_name'] = test.image_name.values
orginin['tags'] = scores
orginin.to_csv('/mnt/home/dunan/Learn/Kaggle/planet_amazon/inceptionv3_origin_result.csv', index=False)
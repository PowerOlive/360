import os
import sys
sys.path.append("..")
os.environ["CUDA_VISIBLE_DEVICES"] = "0"

import tensorflow as tf
config = tf.ConfigProto()
config.gpu_options.allow_growth = True
session = tf.Session(config=config)

from utils.preprocess import *
import keras.backend as K
from utils.data import *
from keras.layers import *
from keras.models import *
from keras.optimizers import *
from keras.callbacks import *
from utils.others import *
from models.deepmodel import *

logging.info("Load Train && Val")
train = pd.read_csv(Config.cache_dir+"/train.csv",sep="\t")
val = pd.read_csv(Config.cache_dir+"/val.csv",sep="\t")

val_word_seq = pickle.load(open(Config.cache_dir+"/g_val_word_seq_%s.pkl"%Config.word_seq_maxlen, "rb"))
val_char_seq = pickle.load(open(Config.cache_dir+"/g_val_char_seq_%s.pkl"%Config.char_seq_maxlen, "rb"))
val_wordp_seq = pickle.load(open(Config.cache_dir+"/g_val_wordp_seq_%s.pkl"%Config.word_seq_maxlen, "rb"))
logging.info("Val Data Load Done.")

batch_size = 32
init_epoch = 0
model_name = "wordp_char_cnn"
trainable_layer = ["word_embedding", "char_embedding"]
train_batch_generator = wordp_char_cnn_train_batch_generator
val_seq = [val_word_seq, val_wordp_seq, val_char_seq]

word_embed_weight = np.load(Config.word_embed_weight_path)
char_embed_weight = np.load(Config.char_embed_weight_path)

val_label = to_categorical(val.label)
model = get_wordp_char_cnn(Config.word_seq_maxlen, Config.char_seq_maxlen, word_embed_weight, char_embed_weight)
#model_path = Config.cache_dir + "/"
#model = load_model(model_path)
logging.info("Model Load Done.")

for i in range(init_epoch, 15):
    if i==6:
        K.set_value(model.optimizer.lr, 0.0001)
    if i==9:
        for l in trainable_layer:
            model.get_layer(l).trainable = True
    model.fit_generator(
        train_batch_generator(train.content.values, train.label.values, batch_size=batch_size),
        epochs = 1,
        steps_per_epoch = int(train.shape[0]/batch_size),
        validation_data = (val_seq, val_label)
    )
    pred = np.squeeze(model.predict(val_seq))
    pre,rec,f1 = score(pred, val_label)
    logging.info("pre: "+ str(pre) + " rec: " + str(rec) + " f1: " + str(f1))
    model.save(Config.cache_dir + "/dp_embed_%s_epoch_%s_%s.h5"%(model_name, i, f1))
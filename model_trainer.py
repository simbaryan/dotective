from ovf_reduced import OVF
from Simulation import FieldSweep
import os
import re
import math
import numpy as np
from numpy import genfromtxt
import pickle
from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import LabelEncoder
from keras import models
from keras import layers
from keras.callbacks import EarlyStopping
from keras.callbacks import ModelCheckpoint
from keras.utils import to_categorical
from timeit import default_timer as timer

DATA_TLD = '/users/PAS1495/simba/simba'
DATA_DIR_ID = '.out'
TEST_TRAIN_SPLIT = 0.2

#Benchmark how long loading the data takes
timer_start = timer()

#Create a list in which to link the spatial data with the cuts
RAWDATA = []

#Instantiate the scaler since these spatial matrices are values on the order of 1e-5 to 1e-8
scl = MinMaxScaler()

for subdir, dirs, files in os.walk(DATA_TLD):
    #Walk through each *.DATA_DIR_ID folder in the DATA_TLD directory
    if DATA_DIR_ID in subdir and DATA_DIR_ID+'/' not in subdir:
        print("------------------------------------------------------------")
        print("Now walking through", subdir)
        #
        #Need the cut position in order to create a labels array
        cut_pos = re.findall("[-+]?[.]?[\d]+(?:,\d\d\d)*[\.]?\d*(?:[eE][-+]?\d+)", subdir)
        if(cut_pos):
            cut_pos = float(cut_pos[0]) #Make sure the scientific notation becomes a float
        else:
            cut_pos = float(-1.0) #If no cut number is found then there is no cut
        #
        #Need a list of all the mf.csv files in the subdir
        Mf_FILES = []
        for i in range(len(files)):
            if '.csv' in files[i] and 'mf' in files[i]:
                Mf_FILES.append(files[i])
        #/for
        #
        #File index probably is not 0, so find out what it is
        file_index = Mf_FILES[0].split("-")[0]
        #
        #Loop through all of the mf.ovf files and process them into magnitudes, which becomes the training data
        for i in range(len(Mf_FILES)):
            i_offset = i+int(file_index) #Handle the file index offset
            print("\nProcessing", Mf_FILES[i])
            #Load magnetization data from the mf.csv file
            mf_csv = genfromtxt(subdir+'/'+Mf_FILES[i], delimiter=',')
            #Scale the spatial data before adding it to the master list
            mf_csv = scl.fit_transform(mf_csv[:,:])
            #Add the spatial grid (inputs) and link it with the cut position (labels)
            RAWDATA.append([mf_csv, cut_pos])
        #/for
    #/if
#/for

#Convert into a Numpy array of shape (n, mx, my)
RAWDATA = np.asarray(RAWDATA)

#Shuffle the master RAWDATA so that training data will be randomized
np.random.shuffle(RAWDATA)

#Master data object starts out as a list structured as <n:{[mx, my]}>
#  n: Range of 0 to total # of resonance datasets
#  mx: 1024 cells wide
#  my: 1024 cells long
DATASET = []
LABELSET = []
for chunk in RAWDATA:
    DATASET.append(chunk[0])
    LABELSET.append(chunk[1])
DATASET = np.asarray(DATASET)
LABELSET = np.asarray(LABELSET)

#Split DATASET into training and testing data, and encode the labels
split_index = len(DATASET) - int(TEST_TRAIN_SPLIT*len(DATASET))
train_grids = DATASET[:split_index,:]
train_labels = LABELSET[:split_index]
test_grids = DATASET[split_index:len(DATASET),:]
test_labels = LABELSET[split_index:len(DATASET)]

#Labelencode the cut positions, and then one-hot encode that result
le = LabelEncoder()
LABELSET_cat = le.fit_transform(LABELSET)
LABELSET_ohe = to_categorical(LABELSET_cat)
train_labels_ohe = LABELSET_ohe[:split_index]
test_labels_ohe = LABELSET_ohe[split_index:len(DATASET)]

#Make sure the shape of the input is correct (the last ",1" is the number of "channels"=1 for grayscale)
train_grids = train_grids.reshape((train_grids.shape[0], 1024, 1024, 1))
test_grids = test_grids.reshape((test_grids.shape[0], 1024, 1024, 1))

#Print the benchmark
timer_end = timer() - timer_start
print("\nTime to run:", str(timer_end/60.0), "mins")

#Network parameters
input_shape = (1024, 1024, 1)
output_size = len(train_labels_ohe[0])
activation = 'relu'
optimizer = 'rmsprop'

#Create the encoder
NETWORK = models.Sequential()

#Layer 1
NETWORK.add(layers.Conv2D(128, (5,5), activation=activation, input_shape=input_shape))

#Pool
NETWORK.add(layers.MaxPooling2D((2,2)))

#Layer 2
NETWORK.add(layers.Conv2D(64, (6,6), activation=activation))

#Pool
NETWORK.add(layers.MaxPooling2D((2,2)))

#Layer 3
NETWORK.add(layers.Conv2D(32, (5,5), activation=activation))

#Pool
NETWORK.add(layers.MaxPooling2D((2,2)))

#Connect to a dense output layer - just like an FCN
NETWORK.add(layers.Flatten())
NETWORK.add(layers.Dense(16, activation=activation))
NETWORK.add(layers.Dense(output_size, activation='softmax'))

#Compile
NETWORK.compile(optimizer=optimizer, loss='categorical_crossentropy', metrics=['accuracy'])

#Save weights
#NETWORK.save_weights('model_weights.h5')

#Print summary
print(NETWORK.summary())

#Fitting parameters
patience = 10
max_epochs = 50
batch_size = 8

#Set callbacks
callbacks = [EarlyStopping(monitor='val_loss', patience=patience),
             ModelCheckpoint(filepath='model_best.h5', monitor='val_loss', save_best_only=True)]

#Fit
history = NETWORK.fit(train_grids, train_labels_ohe,
                        epochs=max_epochs,
                        batch_size=batch_size,
                        callbacks=callbacks,
                        validation_data=(test_grids, test_labels_ohe)
                     )

#Save the history
pickle.dump(history.history, open('model_history.pkl', 'wb'))
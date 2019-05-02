**THE PRIMARY FILE TO VIEW IS:** dotective.ipynb


**ALL DATA IS LOCATED AT:** /fs/scratch/PAS1495/simba/


**SOME ADDITIONAL FILES INCLUDED ARE:**

* dotcleaver.go -- The code written to simulate the dots in MuMax3

* Simulation.py, ovf.py, ovf_reduced.py, lattice.py -- Libraries needed to handle OVF data from MuMax3

* ovf_to_csv.py AND .sh -- Converts MuMax3 OVFs containing spatial data of magnetic components into CSVs containing spatial data of magnetic magnitudes

* model_trainer.py AND .sh -- The code required to train the model as a GPU batch job

* model_best.h5 -- The trained model after running model_trainer.py

* model_history.pkl -- The performance results after running model_trainer.py

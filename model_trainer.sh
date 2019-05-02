#PBS -N model_trainer
#PBS -l walltime=8:00:00
#PBS -l nodes=1:ppn=20:gpus=1
#PBS -j oe

# uncomment if using qsub
cd $PBS_O_WORKDIR
echo $PBS_O_WORKDIR

module load python/3.6-conda5.2
module load cuda/10.0.130
python -u model_trainer.py >&! model_trainer.log
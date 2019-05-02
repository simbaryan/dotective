#PBS -N ovf_to_csv
#PBS -l walltime=2:00:00
#PBS -l nodes=1:ppn=4
#PBS -l mem=4761MB
#PBS -j oe

# uncomment if using qsub
cd $PBS_O_WORKDIR
echo $PBS_O_WORKDIR

module load python/3.6-conda5.2
python -u ovf_to_csv.py >&! ovf_to_csv.log
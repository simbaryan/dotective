from ovf_reduced import OVF
from Simulation import FieldSweep
import os
import re
import math
import numpy as np

DATA_TLD = '/users/PAS1495/simba/simba'
DATA_DIR_ID = '.out'
CUT_OFFSET = 5e-6

#Benchmark how long processing the data takes
timer_start = timer()

for subdir, dirs, files in os.walk(DATA_TLD):
    #Walk through each *.DATA_DIR_ID folder in the DATA_TLD directory
    if DATA_DIR_ID in subdir and DATA_DIR_ID+'/' not in subdir:
        print("------------------------------------------------------------")
        print("Now walking through", subdir)
        #
        #Need the cut position from the folder name so that the cutting region can be zero'd out
        cut_pos = re.findall("[-+]?[.]?[\d]+(?:,\d\d\d)*[\.]?\d*(?:[eE][-+]?\d+)", subdir)
        if(cut_pos):
            cut_pos = float(cut_pos[0])
        else:
            cut_pos = -1
        #
        #Need separate lists of only the m0.ovf and f1-0.ovf files in the subdir
        M0_FILES = []
        F1_FILES = []
        for i in range(len(files)):
            if ('.ovf' and 'm0') in files[i]:
                file_index = files[i].split("-")[0]
                M0_FILES.append(files[i])
                F1_FILES.append(file_index+'-f1-0.ovf')
            #/if
        #/for
        #
        #Instantiate the FieldSweep object to handle the OVF creation (OVFs ONLY)
        #fs = FieldSweep(subdir, file_index)
        #print("File count:", fs.numFiles)
        #print()
        #
        #Open a temporary header file (OVFs ONLY)
        #fs.create_header_file()
        #
        #Loop through all of the found files and process them into mf's (or skip if mf already exists for any given m0/f1 set)
        for i in range(len(M0_FILES)):
            #File index probably is not 0, so find out what it is
            file_index = M0_FILES[i].split("-")[0]
            #
            #################################################################################
            #If the mf exists already, just skip and keep going
            #  Else create the mf out of the m0/f1 pair
            #if fs.check_ovf_files_exist(file_index, '-mf'):
            #    print("\nAlready have ", str(file_index), "-mf.ovf", sep='')
            #    mf_ovf = OVF(subdir, str(file_index)+'-mf.ovf')
            #    mf_ovf.read_m_data()
            #    dM = mf_ovf.m
            #else:
            #    print("\nProcessing ", M0_FILES[i], " and ", F1_FILES[i], "...", sep='')
            #    m0_ovf = OVF(subdir, M0_FILES[i]) #Equilibrium direction of magnetization, which gets subtracted out from final state
            #    m0_ovf.read_m_data()
            #    f1_ovf = OVF(subdir, F1_FILES[i]) #Perturbed direction of magnetization, which is the final system state
            #    f1_ovf.read_m_data()
            #    dM = f1_ovf.m
            #    for j in ['mx','my','mz']:
            #        dM[j] = f1_ovf.m[j] - m0_ovf.m[j] #Change in magnetization from ground state
            #    #/for
            #    fs.save_numpy_array_to_ovf(dM, file_index) #Save evolved state as a new OVF file
            ##/if
            #print(dM[0]) #View just a sample to make sure component values seem correct
            #print()
            #################################################################################
            if str(file_index)+'-mf.csv' in files:
                print("\nAlready have ", str(file_index), "-mf.csv", sep='')
            else:
                print("\nProcessing ", M0_FILES[i], " and ", F1_FILES[i], "...", sep='')
                m0_ovf = OVF(subdir, M0_FILES[i]) #Equilibrium direction of magnetization, which gets subtracted out from final state
                m0_ovf.read_m_data()
                f1_ovf = OVF(subdir, F1_FILES[i]) #Perturbed direction of magnetization, which is the final system state
                f1_ovf.read_m_data()
                dM = f1_ovf.m
                for j in ['mx','my','mz']:
                    dM[j] = f1_ovf.m[j] - m0_ovf.m[j] #Change in magnetization from ground state
                #/for
                #
                #Create an empty grid
                mf = np.empty([1024,1024], dtype=float)
                #Set the zero boundary based on the cutting region's position
                if(cut_pos > 0):
                    zerox = round((cut_pos-CUT_OFFSET - m0_ovf.dx/2.0 + m0_ovf.Nx/2 * m0_ovf.dx) / m0_ovf.dx)
                #Calculate magnetization magnitudes
                for j in range(len(dM)):
                    for k in range(len(dM)):
                        if (cut_pos > 0) and (k >= zerox):
                            mf[j][k] = 0
                        else:
                            mf[j][k] = math.sqrt(dM[j][k][0]**2 + dM[j][k][1]**2 + dM[j][k][2]**2)
                np.savetxt(subdir+'/'+str(file_index)+'-mf.csv', mf, delimiter=',')
                print("\tCreated ", str(file_index), "-mf.csv", "\n\tContains: ", type(mf), " of shape ", mf.shape, "\n\tDatatypes: ", type(mf[0][0]), "\n\tSample: ", mf[0][0], sep='')
            #/if
            #################################################################################
        #/for
        #
        #Remove the temporary header file (OVFs ONLY)
        #fs.delete_header_file()
   #/if
#/for

#Print the benchmark
timer_end = timer() - timer_start
print("\nTime to run:", str(timer_end))
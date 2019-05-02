"""
@author: Simba Ryan
Mumax3 OVF
"""

import os, os.path
import pandas as pd
from ovf_reduced import OVF
import struct

class FieldSweep:
    
    def __init__(self, folderPath, fileIndex=0):
        self.Nx, self.Ny, self.Nz = 0, 0, 0
        self.dx, self.dy, self.dz = 0, 0, 0
        self.xsize, self.ysize, self.zsize = 0, 0, 0
        self.folder = folderPath
        self.filedex = fileIndex
        self.moment = 0
        self.Ms = 0 # 4piMs of material
        self.probe_z = -1
        self.probe_x = -100
        self.numFiles = 0
        self.fileNames = []        
        
        try:
            self.fieldDF = pd.read_csv(folderPath + '/table.txt', sep = '\t')[['FieldNum ()', 'Hext (T)']]
            self.numFieldSteps = len(self.fieldDF['FieldNum ()'])
        except:
            print("Couldn't find table with field values!!!!")
        
        m0_ovf = OVF(folderPath, str(self.filedex)+'-m0.ovf')
        #print(m0_ovf)
        try:
            m0_ovf = OVF(folderPath, str(self.filedex)+'-m0.ovf')
            self.dx = m0_ovf.dx
            self.dy= m0_ovf.dy
            self.dz = m0_ovf.dz
            self.Nx = m0_ovf.Nx
            self.Ny = m0_ovf.Ny
            self.Nz = m0_ovf.Nz
            self.xsize = m0_ovf.xsize
            self.ysize = m0_ovf.ysize
            self.zsize = m0_ovf.zsize
        except:
            print("There wasn't an ovf file to be found!!!!")
             
        self._count_files()
        return
        
        
    def _count_files(self):        
        self.fileNames = [file for file in os.listdir(self.folder) if os.path.isfile(os.path.join(self.folder, file)) and os.path.splitext(file)[1] == '.ovf']
        self.numFiles = len(self.fileNames)
        return 
    
    def check_ovf_files_exist(self, fileIndex, baseName):
        '''Checks if the final configuration file (fileIndex)(baseName).ovf exists.'''
        self._count_files()
        checkFile = str(fileIndex) + str(baseName) + '.ovf'
        for file in self.fileNames:            
            if file == checkFile:
                return True
        return False #didn't find a mf-mz.ovf file
            
    def save_dataframe_to_ovf(self, mzArray, fileIndex):
        '''Saves a pandas DataFrame mzArray to the file (fileIndex)-mz-mf.ovf with the header from a temp file. Make sure header
        temp file is created (with create_header_file) before trying to save!'''
        mfFilePath = os.path.join(self.folder, str(fileIndex) + '-mf-mz.ovf')
        tempFilePath = os.path.join(self.folder, 'temp.ovf')
        if not os.path.isfile(tempFilePath):
            print('No temp header file!')
            return
        
        with open(mfFilePath, 'wb') as mf, open(tempFilePath, 'rb') as temp:
            mf.write(temp.read()) #copy the header and start bytes
            
            for j in range(0, self.Ny):
                for i in range(0, self.Nx):
                    for c in range(0,3):
                        fltByte = struct.pack('f', 0.0) #put 0's for x and y components for now, since I don't have them
                        if c == 2:
                            fltByte = struct.pack('f', mzArray.iloc[(self.Ny-1) - j, i])
                        mf.write(fltByte)
        return
    
    def save_numpy_array_to_ovf(self, array, fileIndex):
        '''Saves a numpy array with slices 'mx', 'my', 'mz' to the file (fileIndex)-mf.ovf with the header from a temp file. Make sure header
        temp file is created (with create_header_file) before trying to save!'''
        mfFilePath = os.path.join(self.folder, str(fileIndex) + '-mf.ovf')
        tempFilePath = os.path.join(self.folder, 'temp.ovf')
        if not os.path.isfile(tempFilePath):
            print('No temp header file!')
            return
        
        with open(mfFilePath, 'wb') as mf, open(tempFilePath, 'rb') as temp:
            mf.write(temp.read()) #copy the header and start bytes
            
            for j in range(0, self.Ny):
                for i in range(0, self.Nx):
                    for c in range(0,3):                        
                        mf.write(struct.pack('f', array[(self.Ny-1) - j, i][c]))
        return
    
    def create_header_file(self):
        '''Creates a temporary file temp.ovf that can be copied when writing data to a new ovf file'''
        with open(self.folder + '/'+str(self.filedex)+'-m0.ovf', 'rb') as m0, open(self.folder + '/temp.ovf', 'wb') as temp:
            ovf = OVF(self.folder, str(self.filedex)+'-m0.ovf')
            temp.write(m0.read(ovf.headerBytes + 4)) #copy the header and start bytes
        return
    
    def delete_header_file(self):
        '''Deletes the temporary header file temp.ovf'''
        if os.path.isfile(os.path.join(self.folder, 'temp.ovf')):
            os.remove(os.path.join(self.folder, 'temp.ovf'))
        else:
            print('temp.ovf did not exist!')
        return